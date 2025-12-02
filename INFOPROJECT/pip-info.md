# РАБОТА С ОФФЛАЙН РЕПО

pip install --no-index --find-links=D:\offline_wheels -r requirements.txt

pip install --no-index --find-links=D:\offline_wheels pandas==2.1.4


# СОЗДАТь локальный мини-репозитарий (локальное зеркало)

python -m http.server 8080

И затем:

pip install --no-index --find-links=http://localhost:8080 wheels/ fastapi