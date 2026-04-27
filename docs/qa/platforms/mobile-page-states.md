# Mobile Page States

Этот документ описывает соответствия между high-level screen detection,
`HomeState` и page/content object классами. Используйте его как источник правды,
когда test user должен прийти на конкретное состояние приложения после
авторизации.

## Auth screens

| Screen | Page object | Назначение |
|---|---|---|
| `MobileScreen.PREVIEW` | `PreviewPage` | Стартовый экран приложения перед вводом телефона. |
| `MobileScreen.PHONE_AUTH` | `PhoneAuthPage` | Экран ввода телефона. |
| `MobileScreen.SMS_CODE` | `SmsCodePage` | Экран ввода SMS-кода. |

Source files:

- [tests/mobile/helpers/screen_detection.py](../../../tests/mobile/helpers/screen_detection.py)
- [src/pages/mobile/auth/preview_page.py](../../../src/pages/mobile/auth/preview_page.py)
- [src/pages/mobile/auth/phone_auth_page.py](../../../src/pages/mobile/auth/phone_auth_page.py)
- [src/pages/mobile/auth/sms_code_page.py](../../../src/pages/mobile/auth/sms_code_page.py)

## Home screens

| Screen | Home state | Content class | Назначение |
|---|---|---|---|
| `MobileScreen.HOME_RABBIT_HOLE` | `HomeState.RABBIT_HOLE` | `HomeRabbitHoleContent` | Главная для пользователя с доступными Rabbit Hole тренировками. |
| `MobileScreen.HOME_NEW_USER` | `HomeState.NEW_USER` | `HomeNewUserContent` | Главная для потенциального пользователя без активных продуктов. |
| `MobileScreen.HOME_SUBSCRIBED` | `HomeState.SUBSCRIBED` | `HomeSubscribedContent` | Главная для пользователя с активной подпиской. |
| `MobileScreen.HOME_MEMBER` | `HomeState.MEMBER` | `HomeMemberContent` | Главная для пользователя с активным service product / абонементом. |

Source files:

- [tests/mobile/helpers/screen_detection.py](../../../tests/mobile/helpers/screen_detection.py)
- [src/pages/mobile/home/home_state.py](../../../src/pages/mobile/home/home_state.py)
- [src/pages/mobile/home/home_page.py](../../../src/pages/mobile/home/home_page.py)
- [src/pages/mobile/home/content/](../../../src/pages/mobile/home/content/)

## HOME_RABBIT_HOLE

- Screen enum: `MobileScreen.HOME_RABBIT_HOLE`
- Home state: `HomeState.RABBIT_HOLE`
- Content class: `HomeRabbitHoleContent`
- Primary marker: `3 КОМБО-ТРЕНИРОВКИ`
- Secondary marker: текст начинается с `Доступны до `
- Detection source:
  - [tests/mobile/helpers/screen_detection.py](../../../tests/mobile/helpers/screen_detection.py)
  - [src/pages/mobile/home/content/home_rabbit_hole_content.py](../../../src/pages/mobile/home/content/home_rabbit_hole_content.py)
  - [src/pages/mobile/home/home_state.py](../../../src/pages/mobile/home/home_state.py)

## HOME_NEW_USER

- Screen enum: `MobileScreen.HOME_NEW_USER`
- Home state: `HomeState.NEW_USER`
- Content class: `HomeNewUserContent`
- Detection source:
  - [tests/mobile/helpers/screen_detection.py](../../../tests/mobile/helpers/screen_detection.py)
  - [src/pages/mobile/home/content/home_new_user_content.py](../../../src/pages/mobile/home/content/home_new_user_content.py)
  - [src/pages/mobile/home/home_state.py](../../../src/pages/mobile/home/home_state.py)

## HOME_SUBSCRIBED

- Screen enum: `MobileScreen.HOME_SUBSCRIBED`
- Home state: `HomeState.SUBSCRIBED`
- Content class: `HomeSubscribedContent`
- Detection source:
  - [tests/mobile/helpers/screen_detection.py](../../../tests/mobile/helpers/screen_detection.py)
  - [src/pages/mobile/home/content/home_subscribed_content.py](../../../src/pages/mobile/home/content/home_subscribed_content.py)
  - [src/pages/mobile/home/home_state.py](../../../src/pages/mobile/home/home_state.py)

## HOME_MEMBER

- Screen enum: `MobileScreen.HOME_MEMBER`
- Home state: `HomeState.MEMBER`
- Content class: `HomeMemberContent`
- Detection source:
  - [tests/mobile/helpers/screen_detection.py](../../../tests/mobile/helpers/screen_detection.py)
  - [src/pages/mobile/home/content/home_member_content.py](../../../src/pages/mobile/home/content/home_member_content.py)
  - [src/pages/mobile/home/home_state.py](../../../src/pages/mobile/home/home_state.py)

## См. также

- [mobile](mobile.md)
- [subscriptions](subscriptions.md)
- [test-data](test-data.md)
- [debugging](debugging.md)
