import socket

import pytest

from app.mcp_connections.service import InvalidMcpEndpoint, validate_endpoint


@pytest.mark.parametrize(
    "url",
    [
        "https://mcp.example.com/mcp",
        "https://MCP.EXAMPLE.COM:443/mcp",
    ],
)
def test_remote_endpoint_accepts_https(url: str) -> None:
    assert validate_endpoint(url, environment="production").startswith("https://")


def test_remote_endpoint_canonicalizes_host_and_default_https_port() -> None:
    assert (
        validate_endpoint(
            "HTTPS://MCP.EXAMPLE.COM:443/Mcp?workspace=South",
            environment="production",
        )
        == "https://mcp.example.com/Mcp?workspace=South"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://mcp.example.com/mcp",
        "https://user:secret@mcp.example.com/mcp",
        "https://mcp.example.com/mcp#fragment",
        "file:///etc/passwd",
        "https:///missing-host",
    ],
)
def test_remote_endpoint_rejects_unsafe_forms(url: str) -> None:
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint(url, environment="production")


@pytest.mark.parametrize(
    "url",
    [
        "https://mcp.example.com/mcp?token=abc",
        "https://mcp.example.com/mcp?api_KEY=abc",
        "https://mcp.example.com/mcp?apikey=abc",
        "https://mcp.example.com/mcp?accesstoken=abc",
        "https://mcp.example.com/mcp?clientSecret=abc",
        "https://mcp.example.com/mcp?clientsecret=abc",
        "https://mcp.example.com/mcp?PASSWORD=abc",
        "https://mcp.example.com/mcp?authorization=abc",
    ],
)
def test_remote_endpoint_rejects_apparent_credentials_in_query(url: str) -> None:
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint(url, environment="production")


@pytest.mark.parametrize("query_key", ["monkey", "author", "hockey"])
def test_remote_endpoint_accepts_non_secret_query_keys_containing_short_terms(
    query_key: str,
) -> None:
    url = f"https://mcp.example.com/mcp?{query_key}=public"

    assert validate_endpoint(url, environment="production") == url


def test_localhost_http_is_development_only() -> None:
    assert validate_endpoint("http://localhost:3001/mcp", environment="development")
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint("http://localhost:3001/mcp", environment="production")


def test_remote_endpoint_rejects_explicit_port_zero() -> None:
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint("https://mcp.example.com:0/mcp", environment="production")


@pytest.mark.parametrize(
    "url",
    [
        "https://mcp%40evil.example.com/mcp",
        "https://mcp%2eexample.com/mcp",
        "https://mcp example.com/mcp",
        " https://mcp.example.com/mcp",
        "https://mcp.example.com\n.evil/mcp",
        "https://mcp.example.com/\x00control",
        "https://mcp.example.com:/mcp",
        "https://bad_host.example.com/mcp",
        "https://-bad.example.com/mcp",
        "https://bad-.example.com/mcp",
        "https://bad..example.com/mcp",
        "https://999.999.999.999/mcp",
        f"https://{'a' * 64}.example.com/mcp",
    ],
)
def test_remote_endpoint_rejects_structurally_invalid_authorities(url: str) -> None:
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint(url, environment="production")


def test_remote_endpoint_normalizes_unicode_dns_hostname_with_idna() -> None:
    assert (
        validate_endpoint("https://B\u00dcCHER.EXAMPLE/mcp", environment="production")
        == "https://xn--bcher-kva.example/mcp"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://192.0.2.10:8443/mcp",
        "https://[2001:db8::1]:8443/mcp",
    ],
)
def test_remote_endpoint_keeps_valid_ip_authorities(url: str) -> None:
    assert validate_endpoint(url, environment="production") == url


def test_structural_validation_never_opens_a_network_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("structural validation attempted outbound network access")

    monkeypatch.setattr(socket, "create_connection", fail_if_called)

    assert (
        validate_endpoint("https://mcp.example.com/mcp", environment="production")
        == "https://mcp.example.com/mcp"
    )
