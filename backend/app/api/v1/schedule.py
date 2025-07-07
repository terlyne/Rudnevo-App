import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from api.deps import get_current_admin_or_superuser
from crud import schedule as schedule_crud
from db.session import get_async_session
from models.user import User
from schemas.schedule import (
    ScheduleTemplateCreate, ScheduleTemplateInDB, ScheduleUploadResponse
)
from utils.schedule_generator import process_excel_schedule, validate_schedule_data

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload-excel", response_model=ScheduleUploadResponse)
async def upload_excel_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Загрузить Excel файл и сгенерировать JSON шаблоны расписаний"""
    try:
        # Проверяем расширение файла
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Поддерживаются только файлы Excel (.xlsx, .xls)"
            )
        
        # Создаем временную папку если её нет
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Сохраняем временный файл
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Обрабатываем файл и получаем JSON данные
        processed_data = await process_excel_schedule(file_path, db)
        
        # Сохраняем шаблоны в базу данных
        templates_to_create = []
        for item in processed_data:
            if validate_schedule_data(item["schedule_data"]) and item.get("college_id"):
                template_data = ScheduleTemplateCreate(
                    college_id=item["college_id"],
                    college_name=item["college_name"],
                    schedule_data=item["schedule_data"],
                    is_active=True
                )
                templates_to_create.append(template_data)
        
        # Деактивируем старые шаблоны для этих колледжей
        for item in processed_data:
            if item.get("college_id"):
                await schedule_crud.deactivate_schedule_templates_by_college_id(
                    db, college_id=item["college_id"]
                )
        
        # Создаем новые шаблоны
        created_templates = await schedule_crud.create_schedule_templates_multi(
            db, templates=templates_to_create
        )
        
        # Удаляем временный файл
        os.remove(file_path)
        
        # Формируем ответ
        result_data = []
        for template in created_templates:
            result_data.append({
                "college": template.college_name,
                "id": template.id,
                "is_active": template.is_active
            })
        
        return ScheduleUploadResponse(
            status="success",
            data=result_data
        )
    
    except Exception as e:
        import traceback
        print('!!! ОШИБКА ПРИ СОХРАНЕНИИ РАСПИСАНИЯ:', repr(e))
        print(traceback.format_exc())
        # Удаляем временный файл в случае ошибки
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки файла: {str(e)}"
        )


@router.get("/templates", response_model=List[ScheduleTemplateInDB])
async def get_schedule_templates(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_async_session)
):
    """Получить список активных шаблонов расписаний с HTML (открытый эндпоинт)"""
    templates = await schedule_crud.get_active_schedule_templates(
        db, skip=skip, limit=limit
    )
    
    # Генерируем HTML для каждого шаблона
    for template in templates:
        schedule_data = template.schedule_data
        schedule = schedule_data.get("schedule", [])
        
        table_html = '''
        <style>
        .schedule-table { max-width: 90%; margin: 20px auto; border-collapse: collapse; }
        .schedule-table th, .schedule-table td { min-height: 80px; height: 80px; padding: 8px; border: 1px solid #ddd; }
        .group-badge { display: inline-block; background:#b6e388; color:#222; font-weight:600; font-size:18px; border-radius:16px; padding:2px 8px; margin:4px 0; text-align:center; }
        .discipline-text { font-size:16px; color:#222; font-weight:500; margin:4px 0; }
        .room-square { display:inline-block; background:#222; color:#fff; font-weight:700; font-size:18px; border-radius:12px; padding:6px 16px; margin:4px 0; }
        .auditory-text { font-size:16px; color:#222; font-weight:500; margin:4px 0; }
        .dates-text { font-size:16px; color:#e74c3c; font-weight:500; margin:4px 0; }
        </style>
        <table class="schedule-table">
            <tr>
                <th>Название</th>
                <th>1 смена <span style="font-size:14px;font-weight:400;">08:15 – 09:50 • 10:30 – 12:05 • 12:15 – 13:50</span></th>
                <th>2 смена <span style="font-size:14px;font-weight:400;">14:15 – 15:50 • 16:30 – 18:05 • 18:15 – 19:50</span></th>
            </tr>
        '''
        
        # Обрабатываем schedule как список записей
        for entry in schedule:
            if isinstance(entry, dict):
                table_html += '<tr>'
                # Первая колонка: группа (зелёный фон), под ней дисциплина (без фона)
                table_html += f'<td>'
                if entry.get("group"):
                    table_html += f'<div class="group-badge">{entry["group"]}</div>'
                if entry.get("discipline"):
                    table_html += f'<div class="discipline-text">{entry["discipline"]}</div>'
                table_html += '</td>'
                
                # 1 смена
                table_html += '<td>'
                if str(entry.get("shift")) == "1":
                    if entry.get("room"):
                        table_html += f'<div class="room-square">{entry["room"]} каб.</div>'
                    if entry.get("auditory"):
                        table_html += f'<div class="auditory-text">{entry["auditory"]}</div>'
                    if entry.get("dates"):
                        table_html += f'<div class="dates-text">{entry["dates"]}</div>'
                table_html += '</td>'
                
                # 2 смена
                table_html += '<td>'
                if str(entry.get("shift")) == "2":
                    if entry.get("room"):
                        table_html += f'<div class="room-square">{entry["room"]} каб.</div>'
                    if entry.get("auditory"):
                        table_html += f'<div class="auditory-text">{entry["auditory"]}</div>'
                    if entry.get("dates"):
                        table_html += f'<div class="dates-text">{entry["dates"]}</div>'
                table_html += '</td>'
                
                table_html += '</tr>'
        
        table_html += '</table>'
        
        # Добавляем HTML в объект шаблона
        template.html_content = table_html
    
    return templates


@router.get("/templates/{college_id}")
async def get_schedule_template_by_college(
    college_id: int, db: AsyncSession = Depends(get_async_session)
):
    """Получить готовый HTML шаблон расписания по college_id (открытый эндпоинт)"""
    template = await schedule_crud.get_schedule_template_by_college_id(
        db, college_id=college_id
    )
    if not template or not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Расписание для данного колледжа не найдено"
        )
    
    schedule_data = template.schedule_data
    schedule = schedule_data.get("schedule", [])
    
    # Отладочная информация
    logger.info(f"=== SCHEDULE DEBUG FOR {college_id} ===")
    logger.info(f"Schedule data type: {type(schedule_data)}")
    logger.info(f"Schedule type: {type(schedule)}")
    logger.info(f"Schedule length: {len(schedule) if isinstance(schedule, list) else 'Not a list'}")
    if isinstance(schedule, list) and schedule:
        first_entry = schedule[0]
        logger.info(f"First entry: {first_entry}")
        logger.info(f"First entry type: {type(first_entry)}")
        logger.info(f"First entry keys: {list(first_entry.keys()) if isinstance(first_entry, dict) else 'Not a dict'}")
        
        # Подробный анализ первой записи
        if isinstance(first_entry, dict):
            for key, value in first_entry.items():
                logger.info(f"  {key}: {value} (type: {type(value)})")

    table_html = '''
    <style>
    .schedule-table { max-width: 90%; margin: 20px auto; border-collapse: collapse; }
    .schedule-table th, .schedule-table td { min-height: 80px; height: 80px; padding: 8px; border: 1px solid #ddd; }
    .group-badge { display: inline-block; background:#b6e388; color:#222; font-weight:600; font-size:18px; border-radius:16px; padding:2px 8px; margin:4px 0; text-align:center; }
    .discipline-text { font-size:16px; color:#222; font-weight:500; margin:4px 0; }
    .room-square { display:inline-block; background:#222; color:#fff; font-weight:700; font-size:18px; border-radius:12px; padding:6px 16px; margin:4px 0; }
    .auditory-text { font-size:16px; color:#222; font-weight:500; margin:4px 0; }
    .dates-text { font-size:16px; color:#e74c3c; font-weight:500; margin:4px 0; }
    </style>
    <table class="schedule-table">
        <tr>
            <th>Название</th>
            <th>1 смена <span style="font-size:14px;font-weight:400;">08:15 – 09:50 • 10:30 – 12:05 • 12:15 – 13:50</span></th>
            <th>2 смена <span style="font-size:14px;font-weight:400;">14:15 – 15:50 • 16:30 – 18:05 • 18:15 – 19:50</span></th>
        </tr>
'''
    
    # Обрабатываем schedule как список записей
    for entry in schedule:
        if isinstance(entry, dict):
            table_html += '<tr>'
            # Первая колонка: группа (зелёный фон), под ней дисциплина (без фона)
            table_html += f'<td>'
            if entry.get("group"):
                table_html += f'<div class="group-badge">{entry["group"]}</div>'
            if entry.get("discipline"):
                table_html += f'<div class="discipline-text">{entry["discipline"]}</div>'
            table_html += '</td>'
            
            # 1 смена
            table_html += '<td>'
            if str(entry.get("shift")) == "1":
                if entry.get("room"):
                    table_html += f'<div class="room-square">{entry["room"]} каб.</div>'
                if entry.get("auditory"):
                    table_html += f'<div class="auditory-text">{entry["auditory"]}</div>'
                if entry.get("dates"):
                    table_html += f'<div class="dates-text">{entry["dates"]}</div>'
            table_html += '</td>'
            
            # 2 смена
            table_html += '<td>'
            if str(entry.get("shift")) == "2":
                if entry.get("room"):
                    table_html += f'<div class="room-square">{entry["room"]} каб.</div>'
                if entry.get("auditory"):
                    table_html += f'<div class="auditory-text">{entry["auditory"]}</div>'
                if entry.get("dates"):
                    table_html += f'<div class="dates-text">{entry["dates"]}</div>'
            table_html += '</td>'
            
            table_html += '</tr>'
    
    table_html += '</table>'
    return HTMLResponse(content=table_html)


@router.delete("/templates/{template_id}")
async def delete_schedule_template(
    *,
    db: AsyncSession = Depends(get_async_session),
    template_id: int,
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Удалить шаблон расписания (только для администраторов)"""
    logger.info(f"=== BACKEND DELETE SCHEDULE TEMPLATE ===")
    logger.info(f"Template ID: {template_id}")
    logger.info(f"Current user: {current_user.username if current_user else 'None'}")
    
    try:
        result = await schedule_crud.delete_schedule_template(db=db, template_id=template_id)
        logger.info(f"CRUD delete result: {result}")
        
        if not result:
            logger.warning(f"Template {template_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Шаблон не найден"
            )
        
        logger.info(f"Template {template_id} deleted successfully")
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error in delete_schedule_template: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@router.delete("/templates")
async def delete_all_schedule_templates(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_admin_or_superuser)
):
    """Удалить все шаблоны расписаний (только для администраторов)"""
    await schedule_crud.delete_all_schedule_templates(db=db)
    return {"ok": True}
