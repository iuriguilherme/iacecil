ia.cecil
===

There is no english README (apart from the tl;dr part below). Sorry 
about that, either learn brazilian portuguese or wait for the 
translation. Millions of people in the internet have been reading in 
english everyday for decades even though that's not their mother 
language. You're smart, you can do it too. If you can't, at least you 
can exercise your patience ;)  

TL;DR
---

Main script uses a mix of MVC design and influence from the python 
frameworks in use's "way to do it (tm)" and resides at _iacecil/_ 
package / directory.  

Plugins are supposed to work as independent scripts and reside at 
_plugins/_ directory.  

Configuration files and local modules / packages are supposed to reside 
at _instance/_ directory.  

The _doc/_ directory is supposed to be helpful but we all know that it 
is impossible. If you don't agree that 100% of github repositories can 
only be understood by it's creator, you're not coding for long enough.  

---

O quê
---

Esta é um chatbot que funciona em múltiplas plataformas baseado em 
plugins e escrito em [Python](https://python.org).  

Por quê
---

O projeto original era a Paloma que era uma chatbot de IRC, e 
posteriormente se tornou bouncer para várias plataformas. Após isto, 
a Paloma virou [MateBot](https://github.com/matehackers/matebot) que é 
um bot de telegram e discord. O escopo do projeto foi ampliado e se 
tornou a IA Cecil (ia.cecil), uma inteligência artificial controlada 
(???) por programação, com uma rede neural simples e acesso a 
algoritmos de aprendizado de máquina.  

Não me pergunte o por quê do nome. Se não for óbvio, eu não quero 
responder.  

Pra quê
---

Toda vez que eu estou entediado, eu escrevo mais um pouco de código 
aqui. Isto acontece desde 2011 (calendário gregoriano).  

Se este projeto virar um produto de uma startup, a culpa não é minha. 
Se este projeto virar uma obra coletiva de tecnocracia, a culpa não é 
minha. Se este projeto virar uma inteligência artificial que cause um 
grande impacto na história da humanidade, a culpa não é minha. Na 
altamente improvável eventualidade de a culpa ser minha, eu espero ser 
avisado a tempo de botar a culpa em quem eu quiser (já que é minha, eu 
faço o que eu quero).  

---

Como
---

### Roadmap

Ver também o arquivo [CHANGES.TXT](./CHANGES.TXT)  

#### [Versão 0.1](https://github.com/iuriguilherme/iacecil/projects/1)

Nível de automata: 
[combinational logic](https://en.wikipedia.org/wiki/Combinational_logic)  

##### Requisitos e escopo

- [ ] Bot deve responder comandos com valores pré definidos  
- [ ] Bot pode ter personalidade fixa configurada previamente e que vai 
perdurar durante todo o seu funcionamento  
- [ ] Novas funcionalidades podem ser acrescentadas através de plugins  
- [ ] Funcionalidades podem ser ativadas ou desativadas de acordo com 
personalidade ou finalidade do bot  
- [ ] Sistema de log para depuração  

##### Funcionalidades

###### Funcionalidades abandonadas

Funcionalidades presentes em forks ou versão **v0.0.14**  

- [x] Conversão de valores [**coinmarketcap**] (**cryptoforex**)  
- [x] Integração com bancos de dados externos [**velivery**] (**vegga**)  
- [x] Envio de SMS e realização de ligações telefônicas [**totalvoice**] 
(**vegga**)  
- [ ] Sistema auxiliar para produção de alimentos [**cr1pt0_almoco**]  
- [x] Integração com ESP32 e monitoramento climático (**climobike**)  
- [x] Controle de atividades de trabalho [**workrave**] (**gê**)  

Funcionalidades presentes em forks ou versão **v0.1.0**  

- [x] Geração de QR Code (**matebot**)  
- [x] Geração de números aleatórios (**matebot**)  
- [x] Cálculo de hash de textos (**matebot**)  
- [x] Recepção de novos usuários em grupos no Telegram (**matebot**)  
- [x] Salvar URLs na Wayback Machine (**matebot**)  
- [x] Download de vídeos do Youtube (**matebot**)  

#### [Versão 0.2](https://github.com/iuriguilherme/iacecil/projects/2)

Nível de automata: 
[finite-state machine](https://en.wikipedia.org/wiki/Finite-state_machine)  

##### Requisitos e escopo

- [ ] Bot deve responder comandos de acordo com regras fixas e 
variáveis conforme aprendizado prévio  
- [ ] Bot deve ter personalidade configurada no estado inicial que pode 
variar e humor que deve variar  
- [ ] Funcionalidades podem ser ativadas ou desativadas de acordo com 
mudança de personalidade, humor ou evento de aprendizado  
- [ ] Sistema de coleta de dados para machine learning  
- [ ] Bot deve funcionar no Telegram e no Discord  

##### Funcionalidades

- [ ] Faz questionários para usuários e armazena as informações em 
banco de dados  
- [ ] Usa dados obtidos para tomar decisões e adicionar pessoas em 
grupos de acordo com critérios estabelecidos  
- [ ] Cria perfil de pessoas através de análise de respostas  
- [ ] Otimiza perfil de pessoas através de análise de comportamento  

### TODO

- [x] Traduzir este README  
  - [ ] Translate the README back to English, Pedro Bó  
- [x] Usar dicionários em todos os retornos de funções  
- [x] Melhorar o empacotamento dos plugins  
- [x] Migrar de telepot para python-telegram-bot _tag v0.1.0.0a_  
- [x] Acrescentar também código para usar com aiogram  _tag v0.1.3.0_
- [ ] Tratar as exceções corretamente, principalmente as informativas  
  - [x] Exceções informativas para quem está tentando instalar o bot do 
    zero suficientemente tratadas e suficientemente informativas com 
    commit 367613a  
  - [ ] Usar Exception Handling do python-telegram-bot  
- [ ] Arquivos para usar com Heroku  
- [x] Arquivos para usar com Docker  
- [ ] Documentar o roadmap com issues, milestones e projetos do github  
  - [x] Issues feitas durante uma Terça Sem Fim

---

Onde
---

Se vossa excelência quiserdes usar o código deste bot pra fazer o vosso 
próprio, vós deveis:  

### Entenderdes e usardes a licença GPL v3

Para mais informações, veja o arquivo [LICENSE.md](./LICENSE.md).  

### Aprenderdes a usar git

...e incidentalmente, Github, Gitlab ou Notabug - que são coisas 
completamente diferentes de git.  

Para mexer no código agora mesmo no Linux:  

```bash
user@home:~$ git clone https://github.com/iuriguilherme/iacecil.git  
user@home:~$ cd iacecil  
user@home:~/iacecil$ pyenv exec python -m pip install --user --upgrade pip pipenv
user@home:~/iacecil$ pipenv install
user@home:~/iacecil$ pipenv run iacecil
```

Se algum dos passos acima não der certo, usardes o vosso próprio método 
pessoal (virtualenv, virtualenvwrapper, poetry, etc.)  

### Grupo de usuária(o)s e desenvolvedora(e)s

Eu criei um grupo novo para quem quiser conversar sobre, usar, testar, 
desenvolver e acompanhar o processo de desenvolvimento, teste e uso da 
bot: <https://t.me/joinchat/CwFUFkf-dKW34FPBjEJs9Q>  

Grupo só para testar bots (pode gerar o caos): 
<https://t.me/joinchat/CwFUFhbgApLHBMLoNnkiRg>  

Grupo para testar o plugin de logs: 
<https://t.me/joinchat/CwFUFhy2NQRi_9Cc60v_aA>  

Pra testar o plugin de logs, coloque o bot neste grupo e use o chat_id 
`-481703172` no arquivo de configuração (_bot.users['special']['log']_)  

---

### Dependências

Este bot foi testado com Python 3.9; Se vós não tiverdes Python, 
[instale!](https://www.python.org/downloads/)  

Estamos usando [FastAPI](https://fastapi.tiangolo.com/), 
[Quart](https://pgjones.gitlab.io/quart/), 
[Aiogram](https://docs.aiogram.dev/en/latest/index.html), 
[Flask](https://flask.palletsprojects.com/), 
[Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot), 
[discordPy](https://discordpy.readthedocs.io/), 
então é necessário instalá-los para rodar o bot.  

Ritual de instalação:  

#### pipenv

O jeito que eu faço é com [pipenv](https://pipenv.pypa.io/), 
inclusive 
está incluso o Pipfile no repositório:  

```bash
user@home:~/iacecil$ python -m ensurepip  
user@home:~/iacecil$ python -m pip install --user --upgrade pip pipenv  
user@home:~/iacecil$ pipenv install  
```

#### Outras formas

Quem não quiser usar pipenv pode usar virtualenvwrapper, virtualenv, 
poetry, ou outro método de preferência se souber o que está fazendo. Um 
arquivo `requirements.txt` é mantido atualizado no repositório.  

```bash
user@home:~/iacecil$ pyenv exec python -m pip install --user -r requirements.txt
```

...ou coisa parecida.  

**TODO**_: Fazer instruções para usar sem pipenv_  

---

### Configurando

Criar o diretório *instance*:  

```bash
user@home:~/iacecil$ mkdir instance
```

Renomear o arquivo `doc/default_config.py` para `instance/config.py`.  

```bash
user@home:~/iacecil$ cp doc/default_config.py instance/config.py
```

Editar o arquivo de configuração, pelo menos adicionando tokens para o valor 
obtido através do [@BotFather](https://t.me/botfather).  

A parte da configuração que é necessário alterar se parece com isto:

```python
'iacecil': {
  ## Obtenha um token com @BotFather no Telegram
  'token': "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
```

Onde **123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11** deve ser substituída 
com a token providenciada pelo BotFather.  

Uma forma alternativa de alterar este campo é diretamente na linha de 
comando usando sed:  

```bash
user@home:~/iacecil$ TOKEN="654321:ZXC-VBN4321ghIkl-zyx57W2v1u123ew11"; sed -i 's/123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/'${TOKEN}'/g' instance/config.py
```

Alterar os demais campos de configuração de acordo com a necessidade, 
cada opção está comentada no arquivo de configuração de exemplo 
`doc/default_config.py`.  

**TODO**_: Documentar exemplos de uso do arquivo de configuração para 
um bot ou vários bots_  

#### Flask / Quart

Para usar a versão com Flask (ou Quart), é necessário também renomear o 
arquivo `doc/default_env` para `.env`. Ou criar um arquivo `.env` com 
as variáveis **FLASK_APP** e **FLASK_ENV** (ou **QUART_APP** / 
**QUART_ENV**).  

---

### Rodando

No diretório principal da *iacecil*:  

#### pipenv

Para rodar com pipenv, assumindo que a configuração já está correta:  

```bash
user@home:~/iacecil$ pipenv run iacecil
```

Se tiver mais bots configuradas, informar o nome da chave do token do 
arquivo de configuração:  

```bash
user@home:~/iacecil$ pipenv run iacecil production
```

O método anterior para usar Flask e python-telegram-bot:  

```bash
user@home:~/iacecil$ pipenv run ptb
```

O método antigo pra usar telepot (não recomendado):  

```bash
user@home:~/iacecil$ pipenv run telepot
```

#### Outros métodos

Quem estiver usando outra coisa que não seja pipenv, pode usar o script 
`app.py` que vai tentar encontrar os módulos e arquivos de configuração 
pertinentes. Alguns exemplos:  

```bash
user@home:~/iacecil$ python3 iacecil aiogram development
```

```bat
C:\Users\user\iacecil> Python app.py flask iacecil
```

Para parar, enviar um sinal *KeyboardInterrupt* (**CTRL+C**).  

---

### Deploy / produção

#### Systemd

Exemplo de arquivo para usar com systemd:  

```systemd
[Unit]
Description=IACecil daemon
After=network.target nss-lookup.target

[Service]
Type=simple
ExecStart=/home/user/.local/bin/pipenv run iacecil
WorkingDirectory=/home/user/iacecil/
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Em um sistema Debian, este arquivo deveria estar em 
`${HOME}/.config/systemd/user/iacecil.service`.  

Habilitando o serviço na inicialização do sistema e iniciando agora:  

```bash
user@home:~$ systemctl --user daemon-reload  
user@home:~$ systemctl --user enable iacecil.service  
user@home:~$ systemctl --user -l start iacecil.service  
```

Para ver se está funcionando:  

```bash
user@home:~$ systemctl --user -l status iacecil.service  
```

Parar:  

```bash
user@home:~$ systemctl --user stop iacecil.service  
```

Remover da inicialização:  

```bash
user@home:~$ systemctl --user disable iacecil.service  
```

Reiniciar:  

```bash
user@home:~$ systemctl --user -l restart iacecil.service  
```

Para o caso de usar systemd como root, o arquivo de configuração deve 
estar em `/lib/systemd/system/iacecil.service`, e os comandos devem ser 
utilizados sem o `--user`, como por exemplo:  

```bash
root@home:/root# systemctl -l restart iacecil.service  
```

Mas eu não recomendo esta abordagem.  

#### Crontab

Também é possível usar cron para verificar se o bot está no ar 
periodicamente:  

```bash
user@home:~$ crontab -e  
```

Adicione uma linha como por exemplo esta na crontab:  

```crontab
*/10 * * * * /usr/lib/systemctl --user is-active iacecil.service || /usr/lib/systemctl --user restart iacecil.service  
```

Isto vai verificar se o bot está no ar a cada 10 minutos, e reiniciar o 
serviço caso esteja fora do ar.  

#### Docker

Adicione seu token em `BOTFATHER_TOKEN` no arquivo `doc/default_env` e 
depois rode os comandos abaixo na raiz do projeto  

 ```bash
 docker build -t matebot -f Dockfile .
 docker run -d --name matebot matebot
 docker inspect matebot | grep IPAddress
 ```

Após esses comandos você terá o IP do seu container pegue esse IP e 
acesse via `CURL IP:5000`  

#### Heroku / Python Anywhere

Existem usuária(o)s do bot que usam Heroku e Python Anywhere 
solicitando ajuda para configurar o robô nestes serviços. Eu nunca usei 
nada disto então preciso de ajuda para tal feito.  

---

Licença
---

Copyleft 2012-2021 Iuri Guilherme <https://iuri.neocities.org/>  

**Este programa é um software livre; você pode redistribuí-lo e/ou**  
**modificá-lo sob os termos da Licença Pública Geral GNU como publicada**  
**pela Free Software Foundation; na versão 3 da Licença, ou**  
**(a seu critério) qualquer versão posterior.**  

**Este programa é distribuído na esperança de que possa ser útil,**  
**mas SEM NENHUMA GARANTIA; sem uma garantia implícita de ADEQUAÇÃO**  
**a qualquer MERCADO ou APLICAÇÃO EM PARTICULAR. Veja a**  
**Licença Pública Geral GNU para mais detalhes.**  

**Você deve ter recebido uma cópia da Licença Pública Geral GNU junto**  
**com este programa (veja o arquivo LICENSE.md).**  
**Se não, veja <http://www.gnu.org/licenses/>.**  
