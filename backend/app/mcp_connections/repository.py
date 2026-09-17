from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.mcp_connections.models import UserMcpConnection


class McpConnectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: UUID) -> list[UserMcpConnection]:
        return list(
            self.session.scalars(
                select(UserMcpConnection)
                .where(UserMcpConnection.user_id == user_id)
                .order_by(UserMcpConnection.created_at, UserMcpConnection.id)
            )
        )

    def get_for_user(
        self,
        connection_id: UUID,
        user_id: UUID,
    ) -> UserMcpConnection | None:
        return self.session.scalar(
            select(UserMcpConnection).where(
                UserMcpConnection.id == connection_id,
                UserMcpConnection.user_id == user_id,
            )
        )

    def create(self, connection: UserMcpConnection) -> UserMcpConnection:
        self.session.add(connection)
        self.session.flush()
        return connection

    def update(self, connection: UserMcpConnection) -> UserMcpConnection:
        self.session.add(connection)
        self.session.flush()
        return connection

    def delete(self, connection: UserMcpConnection) -> None:
        self.session.delete(connection)
        self.session.flush()
