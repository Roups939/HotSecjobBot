import requests
import csv
import time
from bs4 import BeautifulSoup

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

professions = {
    'кибербезопасность': [
        'информационная безопасность',
        'защита информации',
        'безопасность данных',
        'кибербезопасность',
        'cybersecurity',
        'information security',
        'cпециалист по информационной безопасности',
        'application Security Engineer',
        'Information Security Specialist',
        'security Operation Center',
        'пресейл-инженер по информационной безопасности'
    ],
    'DevSecOps': [
        'devSecOps',
        'application security engineer',
        'appSec'
    ],
    'пентестер': [
        'пентестер',
        'pentester',
        'этичный хакер'
    ],
    'антифрод-аналитик': [
        'антифрод-аналитик',
        'антифрод аналитик',
        'SOC аналитик',
        'аналитик безопасности',
        'сетевой аналитик',
        'cпециалист отдела информационной безопасности',
        'инженер отдела ИТ поддержки',
        'сетевой аналитик'
    ],
    'руководитель отдела информационной безопасности': [
        'руководитель отдела информационной безопасности',
        'начальник отдела управления требованиями Службы информационной безопасности',
        'начальник отдела информационных технологий'
    ],
    'аналитик по расследованию компьютерных инцидентов': [
        'аналитик по расследованию компьютерных инцидентов',
        'ведущий специалист по направлению разведки киберугроз',
    ],
    'архитектор информационной безопасности': [
        'Архитектор информационной безопасности',
        'архитектор ИБ',
        'solution architect',
    ]
}

def get_vacancies(keyword, area=1, per_page=10, page_limit=3):
    base_url = 'https://api.hh.ru/vacancies'
    all_vacancies = []

    for page in range(page_limit):
        params = {
            'text': keyword,      # Ключевое слово для поиска
            'area': area,         # Регион
            'per_page': per_page, # Количество вакансий на страницу (макс. 100)
            'page': page          # Текущая страница
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if 'items' not in data:
            break

        all_vacancies.extend(data['items'])
        print(f'Получено {len(data["items"])} вакансий с {page + 1}-й страницы для региона {area}.')

        if (page + 1) >= page_limit:
            break

    return all_vacancies

def get_vacancy_details(vacancy_id):
    url = f'https://api.hh.ru/vacancies/{vacancy_id}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f'Ошибка при запросе вакансии {vacancy_id}: {e}')
        return None

def extract_requirements(description):
    soup = BeautifulSoup(description, 'html.parser')
    return soup.get_text().strip()

def format_salary(salary):
    if salary:
        from_value = salary.get('from', 'не указана')
        to_value = salary.get('to', 'не указана')
        currency = salary.get('currency', '')
        return f"{from_value} - {to_value} {currency}"
    return 'Не указана'

def save_to_csv(vacancies, filename):
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'Название', 'Ссылка', 'Зарплата', 'Локация', 'Требования', 'Профессия', 'Опыт работы'
        ])
        writer.writeheader()

        for vacancy in vacancies:
            writer.writerow({
                'Название': vacancy['name'],
                'Ссылка': vacancy['alternate_url'],
                'Зарплата': format_salary(vacancy['salary']),
                'Локация': vacancy['area']['name'],
                'Требования': vacancy['requirements'],
                'Профессия': vacancy['profession'],
                'Опыт работы': vacancy['experience']
            })

def main():
    while True:
        for region_name, region_id in regions.items():
            all_vacancies = []

            for profession, synonyms in professions.items():
                for spec in synonyms:
                    print(f'Поиск вакансий по специальности: {spec} в регионе {region_name}')
                    vacancies = get_vacancies(keyword=spec, area=region_id, page_limit=3, per_page=10)

                    for vacancy in vacancies:
                        vacancy_details = get_vacancy_details(vacancy['id'])
                        if vacancy_details:
                            requirements = extract_requirements(vacancy_details['description'])
                            all_vacancies.append({
                                'name': vacancy['name'],
                                'alternate_url': vacancy['alternate_url'],
                                'salary': vacancy['salary'],
                                'area': vacancy['area'],
                                'requirements': requirements,
                                'profession': profession,
                                'experience': vacancy_details.get('experience', {}).get('name', 'Не указан')
                            })

            filename = f'{region_id}_vacancies.csv'
            save_to_csv(all_vacancies, filename)
            print(f'Сохранено {len(all_vacancies)} вакансий в файл {filename}')

        print("Ожидание перед следующим обновлением...")
        time.sleep(24 * 60 * 60)  # 24 часов в секундах

if __name__ == '__main__':
    main()
