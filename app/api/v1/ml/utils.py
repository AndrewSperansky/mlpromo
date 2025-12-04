def save_model_stub(path='app/ml/model_catboost.cbm'):
    with open(path,'wb') as f:
        f.write(b'--model-stub--')
