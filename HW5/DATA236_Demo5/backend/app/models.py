from sqlalchemy import String, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Instructor(Base):
    __tablename__ = "instructors"
    __table_args__ = (UniqueConstraint("email", name="uq_instructors_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    courses = relationship("Course", back_populates="instructor")


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("code", name="uq_courses_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # unique
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_available: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    instructor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instructors.id", ondelete="RESTRICT"), nullable=False
    )

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    instructor = relationship("Instructor", back_populates="courses")