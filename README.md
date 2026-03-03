# Como rodar o projeto pelo CMD (Windows)

No momento, este repositório ainda não possui código-fonte da aplicação, apenas a estrutura inicial de versionamento.

Mesmo assim, aqui está um **passo a passo padrão** para você conseguir rodar o projeto assim que os arquivos forem adicionados.

## 1) Instalar pré-requisitos

No Windows, instale:

- [Git](https://git-scm.com/download/win)
- [Node.js LTS](https://nodejs.org/) (se o projeto for JavaScript/TypeScript)
- (Opcional) [Python](https://www.python.org/downloads/) se o projeto usar Python

## 2) Abrir o CMD

- Pressione `Win + R`
- Digite `cmd`
- Pressione `Enter`

## 3) Ir para a pasta onde quer salvar o projeto

Exemplo:

```bat
cd C:\Users\SEU_USUARIO\Documents
```

## 4) Clonar o repositório

```bat
git clone <URL_DO_REPOSITORIO>
cd loja-de-roupas
```

## 5) Verificar qual tecnologia o projeto usa

No CMD, rode:

```bat
dir
```

Procure por arquivos como:

- `package.json` → projeto Node.js
- `requirements.txt` ou `pyproject.toml` → projeto Python
- `pom.xml` → projeto Java (Maven)
- `build.gradle` → projeto Java/Kotlin (Gradle)

## 6) Instalar dependências

### Se for Node.js (`package.json`)

```bat
npm install
```

### Se for Python (`requirements.txt`)

```bat
pip install -r requirements.txt
```

## 7) Rodar o projeto

### Node.js

```bat
npm run dev
```

ou

```bat
npm start
```

### Python

```bat
python main.py
```

## 8) Abrir no navegador (se for aplicação web)

Geralmente o terminal mostrará uma URL como:

- `http://localhost:3000`
- `http://localhost:5173`

Copie e cole no navegador.

## 9) Se der erro, checks rápidos

No CMD:

```bat
node -v
npm -v
git --version
python --version
```

Se quiser, posso montar um passo a passo **100% exato para este projeto** assim que você adicionar os arquivos principais (por exemplo `package.json`, `requirements.txt` ou equivalente).
