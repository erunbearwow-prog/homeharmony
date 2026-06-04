# kitchen/recipe_schema.py
from typing import List, Optional
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str = Field(description="Название ингредиента")
    quantity: Optional[float] = Field(0, description="Количество")
    unit: str = Field(description="Единица измерения (г, мл, шт, ст.л., ч.л.)")


class Step(BaseModel):
    order: int = Field(description="Номер шага")
    instruction: str = Field(description="Описание действия")


class Recipe(BaseModel):
    title: str = Field(description="Название рецепта")
    description: str = Field(default="", description="Описание, советы, примечания")
    ingredients: List[Ingredient] = Field(description="Список ингредиентов")
    steps: List[Step] = Field(description="Список шагов приготовления")