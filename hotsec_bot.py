import logging
import csv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from collections import Counter
import matplotlib.pyplot as plt
import io

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

(
    CHOOSING_MODE, CHOOSING_VACANCY, CHOOSING_REGION, CHOOSING_VACANCY_FOR_SALARY,
    CHOOSING_EXPERIENCE, ENTERING_SALARY, ENTERING_EXPERIENCE
) = range(7)

regions = {
    'москва': 1,
    'санкт-петербург': 2,
    'екатеринбург': 3,
    'новосибирск': 4,
    'нижний новгород': 7,
    'казань': 9,
    'челябинск': 10,
    'самара': 11,
    'омск': 13,
    'ростов-на-дону': 14,
    'уфа': 99,
    'красноярск': 120
}

VACANCIES = [
    'кибербезопасность',
    'DevSecOps',
    'пентестер',
    'антифрод-аналитик',
    'руководитель отдела информационной безопасности',
    'аналитик по расследованию компьютерных инцидентов',
    'архитектор информационной безопасности'
]

EXPERIENCE_OPTIONS = [
    'нет опыта',
    'от 1 года до 3 лет',
    'от 3 до 6 лет',
    'более 6 лет'
]

def read_vacancies_from_csv(region_id):
    filename = f'{region_id}_vacancies.csv'
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError:
        return None

def save_vacancy_to_csv(region_id, vacancy_data):
    filename = f'{region_id}_vacancies.csv'
    fieldnames = ['Название', 'Ссылка', 'Зарплата', 'Локация', 'Требования', 'Профессия', 'Опыт работы']
    try:
        with open(filename, 'a', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(vacancy_data)
    except Exception as e:
        logger.error(f"Ошибка при записи в файл {filename}: {e}")

def calculate_salary_range(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = vacancy['Зарплата']
        if salary and salary != 'Не указана':
            parts = salary.split()
            if len(parts) >= 3:
                try:
                    from_value = float(parts[0]) if parts[0] != 'None' else None
                    to_value = float(parts[2]) if parts[2] != 'None' else None
                    if from_value is not None and to_value is not None:
                        avg_salary = (from_value + to_value) / 2
                        salaries.append(avg_salary)
                except ValueError:
                    continue
    if salaries:
        return min(salaries), max(salaries), sum(salaries) / len(salaries)
    return None, None, None

def analyze_requirements(vacancies):
    requirements = []
    for vacancy in vacancies:
        description = vacancy['Требования']
        if description:
            requirements.append(description.lower())

    skills = [
        'python', 'java', 'c++', 'c#', 'javascript', 'go', 'typescript', 
        'security', 'cloud', 'networking', 'aws', 'azure', 'linux', 'docker', 
        'kubernetes', 'git', 'ci/cd', 'sql', 'mongodb', 'postgresql', 
        'api', 'rest', 'graphql', 'devops', 'microservices'
    ]
    skill_counts = Counter()

    for req in requirements:
        for skill in skills:
            if skill in req:
                skill_counts[skill] += 1

    return skill_counts.most_common(5)

def analyze_experience(vacancies):
    experience_counts = Counter()
    for vacancy in vacancies:
        experience = vacancy.get('Опыт работы', 'Не указан')
        experience_counts[experience] += 1
    return experience_counts.most_common()

def generate_recommendations(common_skills, profession):
    if not common_skills:
        return "Нет данных для рекомендаций."
    profession_recommendations = {
        'кибербезопасность': {
            'базовые': ['python', 'linux', 'networking'],
            'продвинутые': ['aws', 'docker', 'kubernetes'],
            'сертификации': ['CISSP', 'CEH']
        },
        'DevSecOps': {
            'базовые': ['git', 'ci/cd', 'docker'],
            'продвинутые': ['kubernetes', 'aws', 'azure'],
            'сертификации': ['AWS Certified Security', 'Certified Kubernetes Administrator']
        },
        'пентестер': {
            'базовые': ['ethical hacking', 'python', 'networking'],
            'продвинутые': ['penetration testing', 'owasp', 'reverse engineering'],
            'сертификации': ['OSCP', 'CEH']
        },
        'антифрод-аналитик': {
            'базовые': ['data analysis', 'sql', 'python'],
            'продвинутые': ['machine learning', 'big data', 'fraud detection'],
            'сертификации': ['CFE', 'CAMS']
        },
        'руководитель отдела информационной безопасности': {
            'базовые': ['project management', 'risk management', 'compliance'],
            'продвинутые': ['leadership', 'strategic planning', 'budgeting'],
            'сертификации': ['CISSP', 'CISM']
        },
        'аналитик по расследованию компьютерных инцидентов': {
            'базовые': ['forensics', 'incident response', 'networking'],
            'продвинутые': ['malware analysis', 'threat intelligence', 'SIEM'],
            'сертификации': ['GCFA', 'GCIH']
        },
        'архитектор информационной безопасности': {
            'базовые': ['security architecture', 'networking', 'cloud security'],
            'продвинутые': ['zero trust architecture', 'devsecops', 'threat modeling'],
            'сертификации': ['CISSP-ISSAP', 'TOGAF']
        }
    }
    recommendations = profession_recommendations.get(profession.lower(), {})
    top_skills = [skill for skill, _ in common_skills[:3]]
    result = []
    if top_skills:
        result.append(f"Самые востребованные навыки: {', '.join(top_skills)}.")
    
    if recommendations.get('базовые'):
        result.append(f"Базовые навыки: {', '.join(recommendations['базовые'])}.")
    
    if recommendations.get('продвинутые'):
        result.append(f"Продвинутые навыки: {', '.join(recommendations['продвинутые'])}.")
    
    if recommendations.get('сертификации'):
        result.append(f"Рекомендуемые сертификации: {', '.join(recommendations['сертификации'])}.")
    
    return "\n".join(result) if result else "Нет данных для рекомендаций."

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Привет! Выбери режим работы:\n"
        "1. Анализ вакансий по региону\n"
        "2. Анализ зарплат категории по регионам\n\n"
        "Введи номер режима (1 или 2)."
    )
    return CHOOSING_MODE

async def choose_mode(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()
    if user_input == '1':
        await update.message.reply_text(
            "Выбери вакансию из списка:\n"
            "1. Кибербезопасность\n"
            "2. DevSecOps\n"
            "3. Пентестер\n"
            "4. Антифрод-аналитик\n"
            "5. Руководитель отдела информационной безопасности\n"
            "6. Аналитик по расследованию компьютерных инцидентов\n"
            "7. Архитектор информационной безопасности\n\n"
            "Введи номер вакансии (1-7)."
        )
        return CHOOSING_VACANCY
    elif user_input == '2':
        await update.message.reply_text(
            "Выбери специальность для анализа зарплат:\n"
            "1. Кибербезопасность\n"
            "2. DevSecOps\n"
            "3. Пентестер\n"
            "4. Антифрод-аналитик\n"
            "5. Руководитель отдела информационной безопасности\n"
            "6. Аналитик по расследованию компьютерных инцидентов\n"
            "7. Архитектор информационной безопасности\n\n"
            "Введи номер специальности (1-7)."
        )
        return CHOOSING_VACANCY_FOR_SALARY
    else:
        await update.message.reply_text("Пожалуйста, введи 1 или 2.")
        return CHOOSING_MODE

async def choose_vacancy(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()
    if not user_input.isdigit() or int(user_input) < 1 or int(user_input) > 7:
        await update.message.reply_text("Пожалуйста, введи номер вакансии от 1 до 7.")
        return CHOOSING_VACANCY

    vacancy_index = int(user_input) - 1
    context.user_data['vacancy'] = VACANCIES[vacancy_index]

    await update.message.reply_text(
        "Теперь введи регион из доступных:\n"
        "Москва, Санкт-Петербург, Екатеринбург, Новосибирск, Нижний Новгород, Казань, Челябинск, Самара, Омск, Ростов-на-Дону, Уфа, Красноярск."
    )
    return CHOOSING_REGION

async def choose_region(update: Update, context: CallbackContext) -> int:
    region = update.message.text.strip().lower()
    if region not in regions:
        await update.message.reply_text("Указанный регион не поддерживается. Пожалуйста, выбери регион из списка.")
        return CHOOSING_REGION
    context.user_data['region'] = region
    region_id = regions[region]
    vacancies = read_vacancies_from_csv(region_id)
    if not vacancies:
        await update.message.reply_text(f"Для региона {region.title()} нет данных о вакансиях.")
        return ConversationHandler.END
    selected_vacancy = context.user_data['vacancy']
    filtered_vacancies = [v for v in vacancies if selected_vacancy.lower() in v['Профессия'].lower()]
    if not filtered_vacancies:
        await update.message.reply_text(f"В регионе {region.title()} нет вакансий по специальности '{selected_vacancy.title()}'.")
        return ConversationHandler.END
    min_salary, max_salary, avg_salary = calculate_salary_range(filtered_vacancies)
    salary_text = (
        f"Минимальная зарплата: {min_salary:.2f} руб.\n"
        f"Максимальная зарплата: {max_salary:.2f} руб.\n"
        f"Средняя зарплата: {avg_salary:.2f} руб."
    ) if min_salary is not None and max_salary is not None and avg_salary is not None else "Зарплата не указана."

    common_skills = analyze_requirements(filtered_vacancies)
    experience_stats = analyze_experience(filtered_vacancies)
    recommendations = generate_recommendations(common_skills, selected_vacancy)

    experience_text = "Требуемый опыт работы:\n"
    for exp, count in experience_stats:
        experience_text += f"- {exp}: {count} вакансий\n"

    await update.message.reply_text(
        f"Специальность: {selected_vacancy.title()}\n"
        f"Регион: {region.title()}\n"
        f"Найдено вакансий: {len(filtered_vacancies)}\n\n"
        f"{salary_text}\n\n"
        f"{experience_text}\n"
        f"Рекомендации:\n{recommendations}"
    )

    await update.message.reply_text(
        "Если хочешь помочь улучшить данные, укажи свою зарплату и опыт работы.\n"
        "Введи свою зарплату в формате 'от X до Y руб.' (например, 'от 80000 до 120000 руб.'):"
    )
    return ENTERING_SALARY

async def entering_salary(update: Update, context: CallbackContext) -> int:
    salary = update.message.text.strip()
    context.user_data['user_salary'] = salary

    await update.message.reply_text(
        "Теперь укажи свой опыт работы:\n"
        "1. Нет опыта\n"
        "2. От 1 года до 3 лет\n"
        "3. От 3 до 6 лет\n"
        "4. Более 6 лет\n\n"
        "Введи номер опыта работы (1-4)."
    )
    return ENTERING_EXPERIENCE

async def entering_experience(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()
    if not user_input.isdigit() or int(user_input) < 1 or int(user_input) > 4:
        await update.message.reply_text("Пожалуйста, введи номер опыта работы от 1 до 4.")
        return ENTERING_EXPERIENCE

    experience_index = int(user_input) - 1
    experience = EXPERIENCE_OPTIONS[experience_index]
    context.user_data['user_experience'] = experience

    region_id = regions[context.user_data['region']]
    vacancy_data = {
        'Название': f"Пользовательская вакансия ({context.user_data['vacancy']})",
        'Ссылка': 'Не указана',
        'Зарплата': context.user_data['user_salary'],
        'Локация': context.user_data['region'].title(),
        'Требования': 'Не указаны',
        'Профессия': context.user_data['vacancy'],
        'Опыт работы': experience
    }
    save_vacancy_to_csv(region_id, vacancy_data)

    await update.message.reply_text(
        "Спасибо! Твои данные сохранены. Они помогут улучшить анализ вакансий."
    )
    return ConversationHandler.END

async def choose_vacancy_for_salary(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()
    if not user_input.isdigit() or int(user_input) < 1 or int(user_input) > 7:
        await update.message.reply_text("Пожалуйста, введи номер специальности от 1 до 7.")
        return CHOOSING_VACANCY_FOR_SALARY

    vacancy_index = int(user_input) - 1
    selected_vacancy = VACANCIES[vacancy_index]
    context.user_data['vacancy'] = selected_vacancy

    await update.message.reply_text(
        "Выбери требуемый опыт работы:\n"
        "1. Нет опыта\n"
        "2. От 1 года до 3 лет\n"
        "3. От 3 до 6 лет\n"
        "4. Более 6 лет\n\n"
        "Введи номер опыта работы (1-4)."
    )
    return CHOOSING_EXPERIENCE

async def choose_experience(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()
    if not user_input.isdigit() or int(user_input) < 1 or int(user_input) > 4:
        await update.message.reply_text("Пожалуйста, введи номер опыта работы от 1 до 4.")
        return CHOOSING_EXPERIENCE

    experience_index = int(user_input) - 1
    selected_experience = EXPERIENCE_OPTIONS[experience_index]
    context.user_data['experience'] = selected_experience

    region_salaries = {}
    for region_name, region_id in regions.items():
        vacancies = read_vacancies_from_csv(region_id)
        if vacancies:
            filtered_vacancies = [
                v for v in vacancies
                if context.user_data['vacancy'].lower() in v['Профессия'].lower()
                and v.get('Опыт работы', 'Не указан') == selected_experience
            ]
            if filtered_vacancies:
                _, _, avg_salary = calculate_salary_range(filtered_vacancies)
                if avg_salary is not None:
                    region_salaries[region_name] = avg_salary

        if not region_salaries:
        await update.message.reply_text(
            f"Нет данных о зарплатах для специальности '{context.user_data['vacancy'].title()}' "
            f"с опытом работы '{selected_experience}'."
        )
        return ConversationHandler.END

    plt.figure(figsize=(10, 6))
    plt.bar(region_salaries.keys(), region_salaries.values(), color='skyblue')
    plt.xlabel('Регион')
    plt.ylabel('Средняя зарплата (руб)')
    plt.title(
        f'Средние зарплаты для специальности "{context.user_data["vacancy"].title()}"\n'
        f'с опытом работы "{selected_experience}" по регионам'
    )
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    await update.message.reply_photo(
        photo=buf,
        caption=(
            f"Средние зарплаты для специальности '{context.user_data['vacancy'].title()}' "
            f"с опытом работы '{selected_experience}' по регионам."
        )
    )
    plt.close()

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Диалог завершен.")
    return ConversationHandler.END

def main():
    application = Application.builder().token("8143403363:AAEkErlGV0dd5fNa5f8uDd6xXgBSYg6t7aM").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            CHOOSING_VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_vacancy)],
            CHOOSING_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_region)],
            CHOOSING_VACANCY_FOR_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_vacancy_for_salary)],
            CHOOSING_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_experience)],
            ENTERING_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, entering_salary)],
            ENTERING_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, entering_experience)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
