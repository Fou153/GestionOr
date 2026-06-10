# Version mobile - Gestion d'or cassé

Cette version mobile est séparée de l'application PyQt6 bureau. Elle utilise Kivy pour viser Android et garde une base SQLite locale persistante.

## Fonctions incluses

- Page de login.
- Utilisateur par défaut : `admin` / `admin123`.
- Table `clients` séparée.
- Opérations achat/vente attribuées à un client.
- Champ `Carats`.
- Calcul automatique du montant.
- Liste mobile avec couleurs : vente en vert, achat en doré.
- Rapport filtré entre deux dates.
- Base SQLite stockée dans le dossier privé de l'application mobile.

## Lancer sur PC pour tester l'interface

Important : Kivy 2.3.1 supporte Python 3.8 à 3.13. Si votre terminal utilise Python 3.14, l'installation échoue sur Windows avec une erreur proche de `kivy_deps.sdl2_dev`.

Installez Python 3.13 ou Python 3.12, puis créez un environnement virtuel :

```powershell
py -3.13 -m venv .venv-mobile
.\.venv-mobile\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r outputs\mobile_gold_manager\requirements_mobile.txt
python outputs\mobile_gold_manager\main.py
```

Si `py -3.13` ne fonctionne pas, installez Python 3.13 depuis python.org, puis relancez les mêmes commandes.

Pour vérifier la version utilisée :

```powershell
python --version
```

## Générer un APK Android

Buildozer fonctionne mieux sous Linux ou WSL. Depuis le dossier `outputs/mobile_gold_manager` :

```bash
pip install buildozer
buildozer android debug
```

L'APK sera généré dans le dossier `bin`.

## Installer et lancer sur un téléphone Android

Sur Windows, utilisez WSL Ubuntu pour compiler l'APK.

1. Installer WSL Ubuntu depuis PowerShell :

```powershell
wsl --install -d Ubuntu
```

2. Ouvrir Ubuntu, puis installer les outils de compilation :

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git zip unzip openjdk-17-jdk adb
python3 -m pip install --user buildozer cython
```

3. Aller dans le dossier du projet mobile :

```bash
cd /mnt/c/Users/enpei/Documents/Codex/2026-06-08/d-velopper-une-application-de-bureau/outputs/mobile_gold_manager
```

4. Brancher le téléphone avec un câble USB, puis activer sur Android :

- Options développeur ;
- Débogage USB ;
- accepter l'autorisation USB affichée sur le téléphone.

5. Compiler, installer et lancer directement :

```bash
buildozer android debug deploy run
```

Si vous voulez seulement créer le fichier APK :

```bash
buildozer android debug
```

Le fichier sera dans `bin/`. Copiez ensuite l'APK sur le téléphone, ouvrez-le, puis autorisez l'installation depuis une source inconnue si Android le demande.

## Note importante

Sur mobile, la base n'est pas créée à côté du fichier programme. Elle est placée dans le stockage privé de l'application, ce qui évite de perdre les données au redémarrage normal de l'application.
