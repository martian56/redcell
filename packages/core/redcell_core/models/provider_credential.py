from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"
    provider_id: Mapped[str] = mapped_column(String, primary_key=True)
    api_key_enc: Mapped[str] = mapped_column(Text, default="")  # Fernet ciphertext
    api_base: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
