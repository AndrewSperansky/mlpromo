
# Настройки OpenCode

OpenCode является неотъемлемой частью пула  [[AI Agents]]

**Каталог проект: `D:\JS_Projects\3dsonet\.opencode\`**

## Активные ИИ Модели лучше настраивать через десктопную версию OpenCode.

OpenRouter **не прописываем через API key**. Credentials живут отдельно:

```
C:\Users\a.shigaev\.local\share\opencode\auth.json
```

А проектный конфиг отвечает за проект:

```
3dsonet/
├── AGENTS.md
├── .opencode/
│   ├── instructions/
│   └── plugins/
├── .skills/
├── .adr/
└── .prompts/
```

Это правильное разделение **секретов / конфигурации проекта / инструментов AIOS**.


```   
█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █▀▀▀ █▀▀█ █▀▀█ █▀▀█     
█  █ █  █ █▀▀▀ █  █ █    █  █ █  █ █▀▀▀  
▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀  ▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀   
```    
  

## Команды OpenCode

opencode --version  
  
where.exe opencod  
  
```  
Get-ChildItem "$env:USERPROFILE\.opencode" -Recurse -File -ErrorAction SilentlyContinue |  
>>     Select-Object -ExpandProperty FullName  
```  
  
>$env:OPENROUTER_API_KEY="sk-or-v1-972 . . ."  
  
>Get-Content "$env:USERPROFILE\.config\opencode\config.json" -ErrorAction SilentlyContinue  
  
>opencode run --print-logs --log-level DEBUG -m openrouter/minimax/minimax-m3:free "Reply with exactly: OPENROUTER OK"  
  
>opencode debug --help  
  
opencode debug paths  
  
opencode debug config  
  
$env:OPENROUTER_API_KEY  
  
opencode providers login -p openrouter  
  
opencode providers list