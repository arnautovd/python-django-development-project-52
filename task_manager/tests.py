from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Label, Status, Task

User = get_user_model()


@override_settings(ALLOWED_HOSTS=['testserver'])
class UserViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='existing',
            password='Strong-password-123',
            first_name='Existing',
            last_name='User',
        )

    def messages(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_users_list_is_public(self):
        response = self.client.get(reverse('users'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'existing')
        self.assertContains(response, reverse('user_update', args=[self.user.pk]))
        self.assertContains(response, reverse('user_delete', args=[self.user.pk]))

    def test_registration_and_login_pages_are_available(self):
        registration = self.client.get(reverse('user_create'))
        login = self.client.get(reverse('login'))

        self.assertEqual(registration.status_code, 200)
        self.assertEqual(login.status_code, 200)
        for field_name in ('username', 'password1', 'password2'):
            self.assertContains(registration, f'name="{field_name}"')
            self.assertContains(registration, f'id="id_{field_name}"')
        self.assertContains(registration, 'Имя пользователя')
        self.assertContains(registration, 'Пароль')
        self.assertContains(registration, 'Подтверждение пароля')
        self.assertContains(login, 'Имя пользователя')
        self.assertContains(login, 'Пароль')

    def test_user_registration_redirects_to_login(self):
        response = self.client.post(
            reverse('user_create'),
            {
                'first_name': 'New',
                'last_name': 'User',
                'username': 'new-user',
                'password1': 'Strong-password-123',
                'password2': 'Strong-password-123',
            },
        )

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='new-user').exists())
        self.assertIn('Пользователь успешно зарегистрирован', self.messages(response))

    def test_duplicate_username_has_validation_error(self):
        response = self.client.post(
            reverse('user_create'),
            {
                'first_name': 'Duplicate',
                'last_name': 'User',
                'username': 'existing',
                'password1': 'Strong-password-123',
                'password2': 'Strong-password-123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_login_redirects_to_home(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'existing', 'password': 'Strong-password-123'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertIn('Вы залогинены', self.messages(response))

    def test_logout_is_post_only_and_redirects_to_home(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('home'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertIn('Вы разлогинены', self.messages(response))

    def test_anonymous_user_cannot_update(self):
        response = self.client.get(reverse('user_update', args=[self.user.pk]))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("user_update", args=[self.user.pk])}',
        )

    def test_user_can_update_only_themselves(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('user_update', args=[self.user.pk]),
            {
                'first_name': 'Updated',
                'last_name': 'Person',
                'username': 'existing',
            },
        )

        self.assertRedirects(response, reverse('users'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertIn('Пользователь успешно изменен', self.messages(response))

    def test_user_cannot_update_another_user(self):
        other_user = User.objects.create_user(username='other')
        self.client.force_login(self.user)

        response = self.client.get(reverse('user_update', args=[other_user.pk]))

        self.assertRedirects(response, reverse('users'))
        self.assertIn('У вас нет прав для изменения', self.messages(response))

    def test_anonymous_user_cannot_delete(self):
        response = self.client.get(reverse('user_delete', args=[self.user.pk]))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("user_delete", args=[self.user.pk])}',
        )

    def test_authenticated_user_can_delete_user(self):
        self.client.force_login(self.user)
        user_to_delete = User.objects.create_user(username='to-delete')
        response = self.client.post(
            reverse('user_delete', args=[user_to_delete.pk]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=user_to_delete.pk).exists())
        self.assertContains(response, 'Пользователь успешно удален')


@override_settings(ALLOWED_HOSTS=['testserver'])
class StatusViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='status-owner', password='Strong-password-123'
        )
        self.client.force_login(self.user)
        self.status = Status.objects.create(name='Новый')

    def messages(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_status_pages_require_authentication(self):
        self.client.logout()

        for name, args in (
            ('statuses', []),
            ('status_create', []),
            ('status_update', [self.status.pk]),
            ('status_delete', [self.status.pk]),
        ):
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)

    def test_status_list_contains_name_date_and_actions(self):
        response = self.client.get(reverse('statuses'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новый')
        self.assertContains(response, 'Дата создания')
        self.assertContains(response, reverse('status_update', args=[self.status.pk]))
        self.assertContains(response, reverse('status_delete', args=[self.status.pk]))

    def test_status_form_uses_name_field(self):
        response = self.client.get(reverse('status_create'))

        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'id="id_name"')
        self.assertContains(response, 'Имя')

    def test_status_creation_redirects_with_message(self):
        response = self.client.post(
            reverse('status_create'), {'name': 'В работе'}
        )

        self.assertRedirects(response, reverse('statuses'))
        self.assertTrue(Status.objects.filter(name='В работе').exists())
        self.assertIn('Статус успешно создан', self.messages(response))

    def test_duplicate_status_name_has_validation_error(self):
        response = self.client.post(
            reverse('status_create'), {'name': self.status.name}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_status_update_redirects_with_message(self):
        response = self.client.post(
            reverse('status_update', args=[self.status.pk]),
            {'name': 'Завершен'},
        )

        self.assertRedirects(response, reverse('statuses'))
        self.status.refresh_from_db()
        self.assertEqual(self.status.name, 'Завершен')
        self.assertIn('Статус успешно изменен', self.messages(response))

    def test_status_delete_redirects_with_message(self):
        response = self.client.post(
            reverse('status_delete', args=[self.status.pk]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Status.objects.filter(pk=self.status.pk).exists())
        self.assertContains(response, 'Статус успешно удален')

    def test_protected_status_cannot_be_deleted(self):
        error = ProtectedError('protected', [self.status])
        with patch.object(Status, 'delete', side_effect=error):
            response = self.client.post(
                reverse('status_delete', args=[self.status.pk]), follow=True
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Status.objects.filter(pk=self.status.pk).exists())
        self.assertContains(response, 'Невозможно удалить статус')


@override_settings(ALLOWED_HOSTS=['testserver'])
class TaskViewsTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='task-author', password='Strong-password-123'
        )
        self.executor = User.objects.create_user(username='executor')
        self.status = Status.objects.create(name='В работе')
        self.label = Label.objects.create(name='backend')
        self.task = Task.objects.create(
            name='Existing task',
            description='Task description',
            status=self.status,
            author=self.author,
            executor=self.executor,
        )
        self.task.labels.add(self.label)
        self.client.force_login(self.author)

    def messages(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_task_pages_require_authentication(self):
        self.client.logout()

        for name, args in (
            ('tasks', []),
            ('task_create', []),
            ('task_detail', [self.task.pk]),
            ('task_update', [self.task.pk]),
            ('task_delete', [self.task.pk]),
        ):
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)

    def test_task_list_contains_all_required_columns_and_actions(self):
        response = self.client.get(reverse('tasks'))

        self.assertEqual(response.status_code, 200)
        for text in ('Existing task', 'В работе', 'task-author', 'executor'):
            self.assertContains(response, text)
        for name in ('task_detail', 'task_update', 'task_delete'):
            self.assertContains(response, reverse(name, args=[self.task.pk]))

    def test_task_form_has_required_fields_and_labels(self):
        response = self.client.get(reverse('task_create'))

        for field_name in ('name', 'description', 'status', 'executor', 'labels'):
            self.assertContains(response, f'name="{field_name}"')
            self.assertContains(response, f'id="id_{field_name}"')
        for label in ('Имя', 'Описание', 'Статус', 'Исполнитель', 'Метки'):
            self.assertContains(response, label)

    def test_task_creation_sets_author_and_redirects(self):
        response = self.client.post(
            reverse('task_create'),
            {
                'name': 'New task',
                'description': 'New description',
                'status': self.status.pk,
                'executor': self.executor.pk,
                'labels': [self.label.pk],
            },
        )

        self.assertRedirects(response, reverse('tasks'))
        task = Task.objects.get(name='New task')
        self.assertEqual(task.author, self.author)
        self.assertEqual(list(task.labels.all()), [self.label])
        self.assertIn('Задача успешно создана', self.messages(response))

    def test_duplicate_task_name_has_validation_error(self):
        response = self.client.post(
            reverse('task_create'),
            {
                'name': self.task.name,
                'description': 'Duplicate',
                'status': self.status.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_task_update_and_detail(self):
        response = self.client.post(
            reverse('task_update', args=[self.task.pk]),
            {
                'name': 'Updated task',
                'description': 'Updated description',
                'status': self.status.pk,
                'executor': self.executor.pk,
                'labels': [self.label.pk],
            },
        )

        self.assertRedirects(response, reverse('tasks'))
        self.assertIn('Задача успешно изменена', self.messages(response))
        detail = self.client.get(reverse('task_detail', args=[self.task.pk]))
        self.assertContains(detail, 'Updated task')
        self.assertContains(detail, 'backend')

    def test_only_author_can_delete_task(self):
        other_user = User.objects.create_user(username='other-user')
        self.client.force_login(other_user)
        response = self.client.post(
            reverse('task_delete', args=[self.task.pk]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertContains(response, 'Задачу может удалить только ее автор')

    def test_author_can_delete_task(self):
        response = self.client.post(
            reverse('task_delete', args=[self.task.pk]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        self.assertContains(response, 'Задача успешно удалена')

    def test_user_with_tasks_cannot_be_deleted(self):
        response = self.client.post(
            reverse('user_delete', args=[self.author.pk]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.author.pk).exists())
