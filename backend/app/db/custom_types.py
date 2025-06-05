from sqlalchemy.orm import mapped_column
from sqlalchemy import func, String
from datetime import datetime
from typing import Annotated

# Аннотации для моделей БД
int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[
    datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)
]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_false = Annotated[str, mapped_column(String, nullable=False)]
str_uniq_optional = Annotated[str | None, mapped_column(String, unique=True)]
