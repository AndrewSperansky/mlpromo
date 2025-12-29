`uvicorn app.main:app --reload` 
`uvicorn app.main:app --reload --log-level debug`  

`curl http://localhost:8000/`  
`curl http://localhost:8000/routes`  
`curl http://localhost:8000/health`   
`curl http://localhost:8000/api/v1/system/health/server`   
`curl http://localhost:8000/api/v1/system/health/bd`    