from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, dependencies, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.curso_model import CursoModel
from core.deps import get_session

router = APIRouter(
    prefix="/cursos",
    tags=["Cursos"]
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CursoModel,
    summary="Criar um curso"
)
async def create_curso(
    curso: CursoModel,
    session: AsyncSession = Depends(get_session)
) -> CursoModel:
    """
    Cria um novo curso.
    """
    session.add(curso)
    await session.commit()
    await session.refresh(curso)
    return curso

@router.get(
    "/",
    response_model=List[CursoModel],
    summary="Listar cursos"
)
async def get_cursos(
    session: AsyncSession = Depends(get_session)
) -> List[CursoModel]:
    """
    Retorna uma lista de cursos.
    """
    cursos = await session.execute(select(CursoModel))
    return cursos.scalars().all()


@router.get(
    "/{curso_id}",
    response_model=CursoModel,
    summary="Buscar curso por ID"
)
async def get_curso(
    curso_id: int,
    session: AsyncSession = Depends(get_session)
) -> CursoModel:
    """
    Retorna um curso pelo ID.
    """
    curso = await session.get(CursoModel, curso_id)
    if not curso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso não encontrado"
        )
    return curso

@router.put(
    "/{curso_id}",
    response_model=CursoModel,
    summary="Atualizar curso"
)
async def update_curso(
    curso_id: int,
    curso: CursoModel,
    session: AsyncSession = Depends(get_session)
) -> CursoModel:
    """
    Atualiza um curso.
    """
    db_curso = await session.get(CursoModel, curso_id)
    if not db_curso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso não encontrado"
        )
    curso.id = db_curso.id
    session.add(curso)
    await session.commit()
    await session.refresh(curso)
    return curso

@router.delete(
    "/{curso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar curso"
)
async def delete_curso(
    curso_id: int,
    session: AsyncSession = Depends(get_session)
) -> Response:
    """
    Deleta um curso.
    """
    db_curso = await session.get(CursoModel, curso_id)
    if not db_curso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso não encontrado"
        )
    await session.delete(db_curso)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)