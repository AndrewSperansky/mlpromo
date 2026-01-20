### вход  
win+r  
wsl


```
echo $HOME
ls -la $HOME/
ls -la $HOME/.ssh/
mkdir -p $HOME/.ssh && chmod 700 $HOME/.ssh
chmod 700 $HOME/.ssh  # важные права: только для владельца
```

### Просмотр файла
cat $HOME/.ssh/id_ed25519.pub


ssh -T git@github.com

## В GitHub:
Настройки профиля → SSH and GPG keys → New SSH key.
Вставьте ключ, укажите название (например, WSL-Key) и сохраните.