import pytest_check as check
from src.validators.push_notifications.birthday_push_validator import check_birthday_push
import allure


@allure.feature('Notifications')
@allure.story('Birthday Push')
@allure.title('Проверка пуша "С днём рождения"')
@allure.description('Проверяет, что пуш с поздравлением отправлен только пользователям с активной подпиской')
@allure.severity(allure.severity_level.MINOR)
@allure.tag('backend', 'notifications', 'mongodb')
@allure.link(name='MongoDB Query', url='mongodb://localhost:27017')
def test_birthday_push_with_active_users(db):
    """
    Тест проверяет, что пуш с поздравлением 'С днём рождения'
    отправлен только пользователям с активной подпиской.
    """
    with allure.step("Запуск теста Birthday Push"):
        print("=== TEST: Birthday Push ===")
        allure.attach(
            "ENVIRONMENT: PROD\nTEST: Birthday Push Validation",
            name="Test Configuration",
            attachment_type=allure.attachment_type.TEXT
        )
    
    with allure.step("Выполнение проверки Birthday Push"):
        result = check_birthday_push(db)
        
        # Если тест упал, прикрепляем рекомендации
        if not result:
            allure.attach(
                "1. Проверьте ID пользователей в разделе 'Missing IDs'\n"
                "2. Найдите их в MongoDB: db.users.find({_id: ObjectId('...')})\n"
                "3. Проверьте их подписки: db.usersubscriptions.find({user: ObjectId('...')})\n"
                "4. Проверьте birthDate и isActive статус",
                name="How to Debug",
                attachment_type=allure.attachment_type.TEXT
            )