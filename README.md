<p align="center">
  <img src="branding/managerdroid-logo.svg" alt="ManagerDroid" width="420">
</p>

Gerenciador de dispositivos Android para Windows, feito em Python (PySide6) sobre o **ADB**. Permite acompanhar o aparelho, gerenciar aplicativos, remover apps do sistema, espelhar a tela e executar ferramentas do dia a dia, tudo por uma interface em português ou inglês.

> Não exige root. Funciona com depuração USB (ou ADB sem fio) habilitada no aparelho.

---

## Sumário

- [Recursos](#recursos)
- [Telas](#telas)
- [Requisitos](#requisitos)
- [Como usar](#como-usar)
- [Helper do Android](#helper-do-android)
- [Ferramentas externas](#ferramentas-externas)
- [Configurações](#configurações)
- [Compilando o executável](#compilando-o-executável)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Privacidade e segurança](#privacidade-e-segurança)
- [Licença](#licença)

---

## Recursos

### Visão geral do dispositivo
- Modelo, marca (com logo reconhecida), versão do Android, número de série e **patch de segurança** (com alerta de cor conforme a idade: verde até 6 meses, âmbar até 1 ano e vermelho acima disso).
- Monitoramento em tempo real de **armazenamento**, **memória RAM**, **bateria** (nível e temperatura).
- Indicador de uso de RAM do próprio computador na barra de status.

### Aplicativos
- Lista de todos os apps instalados, com **nome e ícone reais**, pacote, tamanho e recomendação.
- Filtros por texto, estado (ativados, desativados, excluídos) e tipo (usuário ou sistema).
- Ações em um ou vários apps de uma vez:
  - desinstalar, desativar e reativar;
  - forçar parada e abrir o app;
  - limpar cache (de um app ou de todos);
  - fazer backup do APK e backup dos dados;
  - ver as permissões concedidas, com descrição em português de cada uma.
- Histórico das alterações feitas pelo programa.
- Atualização inteligente: nomes e ícones só são baixados quando aparece um app novo. Nas atualizações seguintes, a lista carrega quase instantaneamente.

### Remoção de bloatware
- Lista de apps do sistema com **recomendação de remoção** e descrição de cada um.
- Atalhos para selecionar as recomendações ou limpar a seleção.
- Confirmação antes de qualquer remoção.

### Ferramentas
- **Espelhar a tela** com scrcpy (instalado automaticamente na primeira vez).
- **Instalar APK** e pacotes divididos (split), com barra de progresso e opção de cancelamento.
- **Enviar arquivos** para o aparelho.
- **Captura de tela** salva no computador.
- **Resolução e densidade** da tela, com opção de restaurar o padrão.
- **Reiniciar** o aparelho, incluindo modos de recuperação e bootloader.
- **Conexão sem fio** (ADB Wi-Fi).
- **Terminal ADB** interativo.

### Console
- Execução de comandos **ADB** ou **Fastboot**, com ou sem o prefixo (`pm list packages` ou `adb shell pm list packages`).
- Todo comando executado fica registrado no log.

### Interface
- Tema **claro** ou **escuro**, em tons de azul.
- Idioma **português** ou **inglês**.
- Configurações simples: tema e idioma, com ícones SVG.
- Assistente de primeira execução que ensina a ativar o modo desenvolvedor e a depuração USB.

---

## Telas

| Tela | O que faz |
|---|---|
| **Visão geral** | Dados do aparelho, uso de armazenamento, RAM e bateria, e a silhueta do aparelho com a marca |
| **Aplicativos** | Lista de apps, filtros e ações em lote |
| **Ferramentas** | Espelhamento, instalação, arquivos, tela, reinício, Wi-Fi e terminal |
| **Console** | Comandos ADB e Fastboot com log |

---

## Requisitos

- Windows 10 ou 11 (64 bits ou ARM64)
- Python 3.10 ou superior (apenas para executar a partir do código-fonte)
- Aparelho Android com **depuração USB** ativada (Configurações → Opções do desenvolvedor)
- Cabo USB (ou ADB sem fio, no Android 11 ou superior)

Dependências Python (`requirements.txt`):

```text
PySide6>=6.7,<7
psutil>=5.9
```

---

## Como usar

Na primeira vez que o programa é aberto, um assistente explica passo a passo como ativar as **opções do desenvolvedor** e a **depuração USB** no celular. Ele não aparece de novo depois de concluído.

1. Ative a **depuração USB** no aparelho e aceite a chave de depuração que aparecer.
2. Abra o ManagerDroid. Se o ADB não estiver instalado, o programa oferece a instalação automática.
3. Escolha o aparelho no seletor no topo da janela.
4. Use o menu lateral para navegar entre Visão geral, Aplicativos, Ferramentas e Console.

Para executar a partir do código-fonte:

```powershell
py -m pip install -r requirements.txt
py main.py
```

---

## Helper do Android

Para obter nomes e ícones reais dos aplicativos de forma rápida, o ManagerDroid usa um pequeno aplicativo auxiliar instalado no aparelho, o **ManagerDroid Helper** (`com.managerdroid.help`).

- Ele só exporta os dados de que o computador precisa, na pasta `/sdcard/ManagerDroid`.
- Pede a permissão **"Acesso a todos os arquivos"** uma vez, pela própria tela do helper ou pelo ADB.
- Se o helper não estiver instalado, o ManagerDroid pergunta se você quer instalá-lo. Ao confirmar, ele baixa o APK do GitHub do projeto e instala no aparelho. Se a instalação falhar, o APK é enviado para a pasta **Download** do aparelho (`ManagerDroid-Helper.apk`), para você instalar pelo gerenciador de arquivos.
- Sem o helper, o programa ainda funciona, mas mostra os apps pelo nome do pacote (com nomes conhecidos para os principais apps do sistema), sem ícones.

O código-fonte do helper fica em uma pasta separada do projeto, e pode ser compilado com o Android Studio ou com o Gradle.

---

## Ferramentas externas

O ManagerDroid não traz binários de terceiros. Ele procura estas ferramentas e, quando não as encontra, oferece a instalação automática:

| Ferramenta | Origem | Onde fica |
|---|---|---|
| **ADB / Fastboot** (Android Platform Tools) | Google, `dl.google.com` | pasta `adb\` |
| **scrcpy** | Projeto Genymobile, GitHub | pasta `tools\scrcpy\` |

A ordem de busca é: pasta `platform-tools`, pasta `adb`, pasta `tools`, depois o `PATH` do sistema. O programa usa sempre o mesmo `adb` para si e para o scrcpy, evitando conflitos entre versões.

---

## Configurações

Acessadas pelo botão **Configurações** no topo da janela. Há apenas duas opções:

- **Tema**: claro ou escuro
- **Idioma**: português ou inglês

---

## Compilando o executável

O script `build.ps1` gera um executável com PyInstaller:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

O resultado fica em `dist\ManagerDroid\ManagerDroid.exe`.

---

## Estrutura do projeto

```text
managerdroid/
├── main.py              # Aplicativo inteiro (interface e lógica)
├── requirements.txt     # Dependências Python
└── build.ps1            # Script de build (PyInstaller)
```

Arquivos gerados em tempo de execução (não versionar):

- `adb\`, `tools\` e `dist\`: ferramentas baixadas e executável gerado
- Cache, índice de apps e configurações: ficam na pasta de dados do usuário (`%LOCALAPPDATA%`)

---

## Privacidade e segurança

- O programa conversa apenas com o aparelho conectado, pelo ADB, e com os sites oficiais das ferramentas quando faz a instalação automática.
- Não envia dados pessoais para servidores próprios.
- Ações destrutivas (desinstalar, remover apps do sistema, reiniciar em modo de recuperação) pedem confirmação antes de executar.
- Os comandos do console são registrados no log, para auditoria.

---

## Agradecimentos
Agradeço imensamente o Genymobile (criador do scrcpy) por disponibilizar esta ferramenta, se não fosse por ele, o programa não teria funcionalidades incríveis <3

## Licença: MIT
