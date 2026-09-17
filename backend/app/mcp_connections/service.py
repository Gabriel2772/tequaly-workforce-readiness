import re
import unicodedata
from datetime import UTC, datetime
from ipaddress import ip_address
from urllib.parse import parse_qsl, urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy.orm import Session

from app.decisions.models import AuditEvent
from app.mcp_connections.models import UserMcpConnection
from app.mcp_connections.repository import McpConnectionRepository
from app.mcp_connections.schemas import (
    McpConnectionCreate,
    McpConnectionUpdate,
    McpConnectionValidation,
)

_CREDENTIAL_QUERY_TOKENS = frozenset(
    {"token", "key", "secret", "password", "auth", "authorization"}
)
_CREDENTIAL_QUERY_IDENTIFIERS = frozenset(
    {
        "accesstoken",
        "apikey",
        "apitoken",
        "authtoken",
        "bearertoken",
        "clientkey",
        "clientsecret",
        "idtoken",
        "privatekey",
        "refreshtoken",
        "secretkey",
        "subscriptionkey",
        "xapikey",
    }
)
_CONNECTIVITY_FIELDS = frozenset({"client_type", "endpoint_url", "transport"})
_DNS_LABEL_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


class InvalidMcpEndpoint(ValueError):
    pass


class McpConnectionNotFoundError(LookupError):
    pass


def _normalize_hostname(hostname: str) -> str:
    try:
        return ip_address(hostname).compressed.casefold()
    except ValueError:
        pass

    absolute = hostname.endswith(".")
    dns_hostname = hostname[:-1] if absolute else hostname
    try:
        ascii_hostname = dns_hostname.encode("idna").decode("ascii").casefold()
    except UnicodeError as error:
        raise InvalidMcpEndpoint("Endpoint MCP inválido.") from error

    labels = ascii_hostname.split(".")
    if (
        not ascii_hostname
        or len(ascii_hostname) > 253
        or any(_DNS_LABEL_PATTERN.fullmatch(label) is None for label in labels)
        or (len(labels) == 4 and all(label.isdigit() for label in labels))
    ):
        raise InvalidMcpEndpoint("Endpoint MCP inválido.")

    for label in labels:
        if not label.startswith("xn--"):
            continue
        try:
            decoded = label.encode("ascii").decode("idna")
            if decoded.encode("idna").decode("ascii").casefold() != label:
                raise UnicodeError("invalid IDNA label")
        except UnicodeError as error:
            raise InvalidMcpEndpoint("Endpoint MCP inválido.") from error

    return f"{ascii_hostname}." if absolute else ascii_hostname


def validate_endpoint(endpoint_url: str, *, environment: str) -> str:
    candidate = endpoint_url
    if not candidate or any(
        character.isspace() or unicodedata.category(character) == "Cc"
        for character in candidate
    ):
        raise InvalidMcpEndpoint("Endpoint MCP inválido.")
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as error:
        raise InvalidMcpEndpoint("Endpoint MCP inválido.") from error

    if port == 0:
        raise InvalidMcpEndpoint("Endpoint MCP inválido.")

    scheme = parsed.scheme.casefold()
    hostname = parsed.hostname
    if (
        hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or "#" in candidate
        or "%" in parsed.netloc
        or parsed.netloc.endswith(":")
    ):
        raise InvalidMcpEndpoint("Endpoint MCP inválido.")
    hostname = _normalize_hostname(hostname)

    is_development_localhost = (
        scheme == "http" and hostname == "localhost" and environment == "development"
    )
    if scheme != "https" and not is_development_localhost:
        raise InvalidMcpEndpoint("O endpoint MCP deve usar HTTPS.")

    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        separated_key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
        query_tokens = {
            token
            for token in re.split(r"[^a-z0-9]+", separated_key.casefold())
            if token
        }
        normalized_key = re.sub(r"[^a-z0-9]+", "", key.casefold())
        if (
            query_tokens & _CREDENTIAL_QUERY_TOKENS
            or normalized_key in _CREDENTIAL_QUERY_IDENTIFIERS
        ):
            raise InvalidMcpEndpoint("A URL do endpoint não pode conter credenciais.")

    canonical_host = f"[{hostname}]" if ":" in hostname else hostname
    canonical_port = (
        "" if port is None or (scheme == "https" and port == 443) else f":{port}"
    )
    canonical_netloc = f"{canonical_host}{canonical_port}"
    return urlunsplit((scheme, canonical_netloc, parsed.path, parsed.query, ""))


class McpConnectionService:
    def __init__(
        self,
        session: Session,
        *,
        user_id: UUID,
        actor_id: str,
        environment: str,
    ) -> None:
        self._session = session
        self._repository = McpConnectionRepository(session)
        self._user_id = user_id
        self._actor_id = actor_id
        self._environment = environment

    def list_for_user(self) -> list[UserMcpConnection]:
        return self._repository.list_for_user(self._user_id)

    def create(self, command: McpConnectionCreate) -> UserMcpConnection:
        connection = UserMcpConnection(
            user_id=self._user_id,
            name=command.name,
            client_type=command.client_type,
            endpoint_url=validate_endpoint(
                command.endpoint_url,
                environment=self._environment,
            ),
            transport=command.transport,
            notes=command.notes,
            enabled=command.enabled,
            last_validated_at=None,
        )
        self._repository.create(connection)
        self._audit("mcp_connection.created", connection)
        return connection

    def update(
        self,
        connection_id: UUID,
        command: McpConnectionUpdate,
    ) -> UserMcpConnection:
        connection = self._require_connection(connection_id)
        updates = command.model_dump(exclude_unset=True)
        endpoint_url = updates.get("endpoint_url")
        if isinstance(endpoint_url, str):
            updates["endpoint_url"] = validate_endpoint(
                endpoint_url,
                environment=self._environment,
            )
        if any(
            field in updates and updates[field] != getattr(connection, field)
            for field in _CONNECTIVITY_FIELDS
        ):
            connection.last_validated_at = None
        for field, value in updates.items():
            setattr(connection, field, value)
        self._repository.update(connection)
        self._audit("mcp_connection.updated", connection)
        return connection

    def validate(self, connection_id: UUID) -> McpConnectionValidation:
        connection = self._require_connection(connection_id)
        normalized_endpoint_url = validate_endpoint(
            connection.endpoint_url,
            environment=self._environment,
        )
        validated_at = datetime.now(UTC)
        connection.endpoint_url = normalized_endpoint_url
        connection.last_validated_at = validated_at
        self._repository.update(connection)
        self._audit("mcp_connection.validated", connection)
        return McpConnectionValidation(
            valid=True,
            normalized_endpoint_url=normalized_endpoint_url,
            validated_at=validated_at,
        )

    def delete(self, connection_id: UUID) -> None:
        connection = self._require_connection(connection_id)
        self._audit("mcp_connection.deleted", connection)
        self._repository.delete(connection)

    def _require_connection(self, connection_id: UUID) -> UserMcpConnection:
        connection = self._repository.get_for_user(connection_id, self._user_id)
        if connection is None:
            raise McpConnectionNotFoundError(str(connection_id))
        return connection

    def _audit(self, event_type: str, connection: UserMcpConnection) -> None:
        self._session.add(
            AuditEvent(
                actor_id=self._actor_id,
                event_type=event_type,
                aggregate_type="mcp_connection",
                aggregate_id=connection.id,
                payload={
                    "client_type": connection.client_type,
                    "transport": connection.transport,
                    "enabled": connection.enabled,
                },
                occurred_at=datetime.now(UTC),
            )
        )
        self._session.flush()
