# Як запустити та вигрузити скрапер на GitHub

## 1. Створити репозиторій на GitHub

1. Перейти на https://github.com/new
2. Назва: `keycrm-scraper`
3. Обрати **Public**
4. Натиснути **Create repository**

---

## 2. Завантажити код на GitHub

Відкрити термінал і виконати:

```bash
cd "C:\Users\TW-25\Documents\Проекти\Scrap"

git init
git add .
git commit -m "KeyCRM scraper"

git remote add origin https://github.com/YOUR_USERNAME/keycrm-scraper.git
git branch -M main
git push -u origin main
```

*(Замінити YOUR_USERNAME на твій логін)*

---

## 3. ДодатиSecrets (налаштування)

Після публікації репозиторію:

1. Перейти в репозиторій на GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Натиснути **New repository secret** і додати:

| Secret | Значення |
|--------|----------|
| `KEYCRM_URL` | `https://backstageart.keycrm.app/` |
| `KEYCRM_USERNAME` | твій логін |
| `KEYCRM_PASSWORD` | твій пароль |
| `AIVEN_PG_HOST` | хост з Aiven |
| `AIVEN_PG_PORT` | порт |
| `AIVEN_PG_DB` | `defaultdb` |
| `AIVEN_PG_USER` | `avnadmin` |
| `AIVEN_PG_PASSWORD` | пароль з Aiven |
| `AIVEN_PG_SSLMODE` | `require` |

---

## 4. Запуск скрапера

### Варіант А: Вручну через GitHub

1. Перейти у вкладку **Actions**
2. Обрати **Run KeyCRM Scraper**
3. Натиснути **Run workflow**

### Варіант Б: Локально

```bash
python -m scraper.cli --headless
```

---

## Готово!