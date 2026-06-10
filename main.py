import hashlib
import sqlite3
from datetime import date
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


GOLD = (0.83, 0.68, 0.22, 1)
DARK = (0.08, 0.08, 0.08, 1)
PAPER = (0.96, 0.94, 0.89, 1)
WHITE = (1, 1, 1, 1)
GREEN_ROW = (0.84, 0.95, 0.87, 1)
GOLD_ROW = (1.0, 0.92, 0.68, 1)
RED = (0.78, 0.22, 0.22, 1)
GREEN = (0.13, 0.52, 0.27, 1)
TEXT = (0.12, 0.12, 0.12, 1)
MUTED = (0.38, 0.38, 0.38, 1)


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.path)

    def init_db(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    telephone TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_operation TEXT NOT NULL,
                    client_id INTEGER NOT NULL,
                    ayar TEXT,
                    poids REAL NOT NULL,
                    prix_gramme REAL NOT NULL,
                    montant REAL NOT NULL,
                    date_operation TEXT NOT NULL,
                    FOREIGN KEY(client_id) REFERENCES clients(id)
                )
                """
            )
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if user_count == 0:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    ("admin", self.hash_password("admin123")),
                )

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(f"gold-manager::{password}".encode("utf-8")).hexdigest()

    def verify_user(self, username, password):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username=?",
                (username,),
            ).fetchone()
        return bool(row and row[0] == self.hash_password(password))

    def add_client(self, nom, prenom, telephone):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO clients (nom, prenom, telephone) VALUES (?, ?, ?)",
                (nom.strip(), prenom.strip(), telephone.strip()),
            )

    def list_clients(self, search=""):
        query = "SELECT id, nom, prenom, telephone FROM clients"
        params = []
        if search:
            query += " WHERE nom LIKE ? OR prenom LIKE ? OR telephone LIKE ?"
            params = [f"%{search}%", f"%{search}%", f"%{search}%"]
        query += " ORDER BY nom, prenom"
        with self.connect() as conn:
            return conn.execute(query, params).fetchall()

    def client_labels(self):
        rows = self.list_clients()
        labels = {}
        for client_id, nom, prenom, telephone in rows:
            label = f"{nom} {prenom} - {telephone}"
            labels[label] = client_id
        return labels

    def add_transaction(self, type_operation, client_id, ayar, poids, prix_gramme, date_operation):
        montant = poids * prix_gramme
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO transactions
                (type_operation, client_id, ayar, poids, prix_gramme, montant, date_operation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (type_operation, client_id, ayar, poids, prix_gramme, montant, date_operation),
            )

    def delete_transaction(self, transaction_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))

    def list_transactions(self, limit=50):
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT t.id, t.type_operation, c.nom, c.prenom, c.telephone, t.ayar,
                       t.poids, t.prix_gramme, t.montant, t.date_operation
                FROM transactions t
                JOIN clients c ON c.id = t.client_id
                ORDER BY t.date_operation DESC, t.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def report(self, date_from, date_to):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT t.id, t.type_operation, c.nom, c.prenom, c.telephone, t.ayar,
                       t.poids, t.prix_gramme, t.montant, t.date_operation
                FROM transactions t
                JOIN clients c ON c.id = t.client_id
                WHERE t.date_operation BETWEEN ? AND ?
                ORDER BY t.date_operation DESC, t.id DESC
                """,
                (date_from, date_to),
            ).fetchall()
        total_buy = sum(row[8] for row in rows if row[1] == "Achat")
        total_sell = sum(row[8] for row in rows if row[1] == "Vente")
        return rows, total_buy, total_sell, total_sell - total_buy


class Card(BoxLayout):
    bg_color = ListProperty(WHITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(12)
        self.spacing = dp(8)
        with self.canvas.before:
            Color(rgba=self.bg_color)
            self.rect = RoundedRectangle(radius=[dp(12)], pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect, bg_color=self.update_color)

    def update_rect(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_color(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.bg_color)
            self.rect = RoundedRectangle(radius=[dp(12)], pos=self.pos, size=self.size)


def label(text, size=14, color=TEXT, bold=False, height=None):
    item = Label(
        text=text,
        color=color,
        font_size=dp(size),
        bold=bold,
        halign="left",
        valign="middle",
    )
    item.bind(size=lambda widget, *_: setattr(widget, "text_size", widget.size))
    if height:
        item.size_hint_y = None
        item.height = dp(height)
    return item


def input_field(hint, password=False):
    return TextInput(
        hint_text=hint,
        password=password,
        multiline=False,
        size_hint_y=None,
        height=dp(48),
        background_color=WHITE,
        foreground_color=TEXT,
        cursor_color=GOLD,
        padding=(dp(12), dp(12)),
    )


def action_button(text, color=GOLD):
    return Button(
        text=text,
        size_hint_y=None,
        height=dp(48),
        background_normal="",
        background_color=color,
        color=(0.05, 0.05, 0.05, 1) if color == GOLD else WHITE,
        bold=True,
    )


def show_message(title, message):
    content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
    content.add_widget(label(message, size=15))
    close = action_button("OK")
    content.add_widget(close)
    popup = Popup(title=title, content=content, size_hint=(0.86, None), height=dp(220))
    close.bind(on_release=popup.dismiss)
    popup.open()


class BaseScreen(Screen):
    def page(self, title):
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), spacing=dp(8))
        header.add_widget(label(title, size=22, color=GOLD, bold=True))
        logout = Button(
            text="Sortir",
            size_hint=(None, None),
            size=(dp(82), dp(42)),
            background_normal="",
            background_color=DARK,
            color=WHITE,
            bold=True,
        )
        logout.bind(on_release=lambda *_: self.logout())
        header.add_widget(logout)
        root.add_widget(header)
        return root

    def nav(self):
        tabs = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(6))
        items = [
            ("Clients", "clients"),
            ("Opérations", "transactions"),
            ("Rapport", "report"),
        ]
        for text, screen_name in items:
            btn = Button(
                text=text,
                background_normal="",
                background_color=GOLD if self.name == screen_name else DARK,
                color=(0.05, 0.05, 0.05, 1) if self.name == screen_name else WHITE,
                bold=True,
            )
            btn.bind(on_release=lambda _btn, name=screen_name: self.goto(name))
            tabs.add_widget(btn)
        return tabs

    def goto(self, name):
        self.manager.current = name

    def logout(self):
        self.manager.current = "login"

    @property
    def db(self):
        return App.get_running_app().db


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        root.add_widget(label("Gestion d'or cassé", size=26, color=GOLD, bold=True, height=68))
        card = Card(orientation="vertical", bg_color=WHITE, size_hint_y=None, height=dp(300))
        card.add_widget(label("Connexion", size=22, bold=True, height=42))
        self.username = input_field("Nom d'utilisateur")
        self.password = input_field("Mot de passe", password=True)
        card.add_widget(self.username)
        card.add_widget(self.password)
        login_btn = action_button("Se connecter")
        login_btn.bind(on_release=self.login)
        card.add_widget(login_btn)
        card.add_widget(label("Utilisateur par défaut : admin / admin123", size=12, color=MUTED, height=32))
        root.add_widget(card)
        root.add_widget(label("Les données sont gardées dans le stockage privé de l'application.", size=13, color=MUTED))
        self.add_widget(root)

    @property
    def db(self):
        return App.get_running_app().db

    def login(self, *_):
        if self.db.verify_user(self.username.text.strip(), self.password.text.strip()):
            self.password.text = ""
            self.manager.current = "transactions"
        else:
            show_message("Erreur", "Identifiants incorrects.")


class ClientsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = self.page("Clients")

        form = Card(orientation="vertical", bg_color=WHITE, size_hint_y=None, height=dp(270))
        self.nom = input_field("Nom")
        self.prenom = input_field("Prénom")
        self.telephone = input_field("Téléphone")
        form.add_widget(self.nom)
        form.add_widget(self.prenom)
        form.add_widget(self.telephone)
        save = action_button("Ajouter le client")
        save.bind(on_release=self.save_client)
        form.add_widget(save)
        root.add_widget(form)

        self.search = input_field("Recherche client")
        self.search.bind(text=lambda *_: self.refresh())
        root.add_widget(self.search)

        self.list_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        root.add_widget(self.nav())
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def save_client(self, *_):
        nom = self.nom.text.strip()
        prenom = self.prenom.text.strip()
        telephone = self.telephone.text.strip()
        if not nom or not prenom or not telephone:
            show_message("Erreur", "Veuillez remplir nom, prénom et téléphone.")
            return
        try:
            self.db.add_client(nom, prenom, telephone)
        except sqlite3.IntegrityError:
            show_message("Erreur", "Ce numéro de téléphone existe déjà.")
            return
        self.nom.text = ""
        self.prenom.text = ""
        self.telephone.text = ""
        self.refresh()
        show_message("Succès", "Client ajouté.")

    def refresh(self):
        self.list_box.clear_widgets()
        for _client_id, nom, prenom, telephone in self.db.list_clients(self.search.text.strip()):
            card = Card(orientation="vertical", bg_color=WHITE, size_hint_y=None, height=dp(82))
            card.add_widget(label(f"{nom} {prenom}", size=16, bold=True, height=28))
            card.add_widget(label(telephone, size=13, color=MUTED, height=24))
            self.list_box.add_widget(card)


class TransactionsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = self.page("Opérations")

        form = Card(orientation="vertical", bg_color=WHITE, size_hint_y=None, height=dp(410))
        self.client_spinner = Spinner(text="Sélectionner un client", values=[], size_hint_y=None, height=dp(48))
        self.type_spinner = Spinner(text="Achat", values=["Achat", "Vente"], size_hint_y=None, height=dp(48))
        self.ayar_spinner = Spinner(text="18", values=["24", "22", "21", "18", "14"], size_hint_y=None, height=dp(48))
        row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(48))
        self.poids = input_field("Poids (g)")
        self.prix = input_field("Prix gramme")
        row.add_widget(self.poids)
        row.add_widget(self.prix)
        self.date_operation = input_field("Date YYYY-MM-DD")
        self.date_operation.text = date.today().isoformat()
        self.amount_label = label("Montant : 0.00 DA", size=18, color=GOLD, bold=True, height=42)

        self.poids.bind(text=lambda *_: self.calculate())
        self.prix.bind(text=lambda *_: self.calculate())

        form.add_widget(self.client_spinner)
        form.add_widget(self.type_spinner)
        form.add_widget(self.ayar_spinner)
        form.add_widget(row)
        form.add_widget(self.date_operation)
        form.add_widget(self.amount_label)
        save = action_button("Enregistrer")
        save.bind(on_release=self.save_transaction)
        form.add_widget(save)
        root.add_widget(form)

        self.list_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        root.add_widget(self.nav())
        self.add_widget(root)
        self.client_map = {}

    def on_pre_enter(self, *_):
        self.refresh_clients()
        self.refresh_transactions()

    def refresh_clients(self):
        self.client_map = self.db.client_labels()
        values = list(self.client_map.keys())
        self.client_spinner.values = values
        if values and self.client_spinner.text not in values:
            self.client_spinner.text = values[0]
        if not values:
            self.client_spinner.text = "Créer un client d'abord"

    def calculate(self):
        try:
            poids = float((self.poids.text or "0").replace(",", "."))
            prix = float((self.prix.text or "0").replace(",", "."))
        except ValueError:
            poids = 0
            prix = 0
        self.amount_label.text = f"Montant : {poids * prix:,.2f} DA"

    def save_transaction(self, *_):
        if self.client_spinner.text not in self.client_map:
            show_message("Erreur", "Veuillez créer ou sélectionner un client.")
            return
        try:
            poids = float(self.poids.text.replace(",", "."))
            prix = float(self.prix.text.replace(",", "."))
        except ValueError:
            show_message("Erreur", "Poids et prix doivent être numériques.")
            return
        if poids <= 0 or prix <= 0 or not self.date_operation.text.strip():
            show_message("Erreur", "Veuillez compléter les champs obligatoires.")
            return
        self.db.add_transaction(
            self.type_spinner.text,
            self.client_map[self.client_spinner.text],
            self.ayar_spinner.text,
            poids,
            prix,
            self.date_operation.text.strip(),
        )
        self.poids.text = ""
        self.prix.text = ""
        self.calculate()
        self.refresh_transactions()
        show_message("Succès", "Opération enregistrée.")

    def refresh_transactions(self):
        self.list_box.clear_widgets()
        for row in self.db.list_transactions():
            self.list_box.add_widget(TransactionCard(row, self.delete_transaction))

    def delete_transaction(self, transaction_id):
        self.db.delete_transaction(transaction_id)
        self.refresh_transactions()


class TransactionCard(Card):
    def __init__(self, row, on_delete=None, **kwargs):
        bg = GREEN_ROW if row[1] == "Vente" else GOLD_ROW
        super().__init__(orientation="vertical", bg_color=bg, size_hint_y=None, height=dp(132), **kwargs)
        transaction_id, type_operation, nom, prenom, telephone, ayar, poids, prix, montant, tx_date = row
        title = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(34))
        title.add_widget(label(f"{type_operation} - {nom} {prenom}", size=16, bold=True))
        if on_delete:
            delete = Button(
                text="Supprimer",
                size_hint=(None, None),
                size=(dp(96), dp(34)),
                background_normal="",
                background_color=RED,
                color=WHITE,
            )
            delete.bind(on_release=lambda *_: on_delete(transaction_id))
            title.add_widget(delete)
        self.add_widget(title)
        self.add_widget(label(f"{telephone} | Carats {ayar} | {tx_date}", size=12, color=MUTED, height=24))
        self.add_widget(label(f"{poids:.2f} g x {prix:.2f} DA", size=13, height=24))
        self.add_widget(label(f"{montant:,.2f} DA", size=18, bold=True, height=34))


class ReportScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = self.page("Rapport")

        filters = Card(orientation="vertical", bg_color=WHITE, size_hint_y=None, height=dp(210))
        self.date_from = input_field("Du YYYY-MM-DD")
        self.date_to = input_field("Au YYYY-MM-DD")
        today = date.today().isoformat()
        self.date_from.text = today
        self.date_to.text = today
        filters.add_widget(self.date_from)
        filters.add_widget(self.date_to)
        refresh = action_button("Afficher")
        refresh.bind(on_release=lambda *_: self.refresh())
        filters.add_widget(refresh)
        root.add_widget(filters)

        totals = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, height=dp(174))
        self.buy_total = self.total_card("Achats", RED)
        self.sell_total = self.total_card("Ventes", GREEN)
        self.profit_total = self.total_card("Bénéfice", GOLD)
        totals.add_widget(self.buy_total)
        totals.add_widget(self.sell_total)
        totals.add_widget(self.profit_total)
        root.add_widget(totals)

        self.list_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        root.add_widget(self.nav())
        self.add_widget(root)

    def total_card(self, title, color):
        card = Card(orientation="horizontal", bg_color=WHITE, size_hint_y=None, height=dp(52))
        card.add_widget(label(title, size=14, color=MUTED, bold=True))
        value = label("0.00 DA", size=16, color=color, bold=True)
        card.add_widget(value)
        card.value = value
        return card

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        date_from = self.date_from.text.strip()
        date_to = self.date_to.text.strip()
        if not date_from or not date_to:
            show_message("Erreur", "Veuillez saisir les deux dates.")
            return
        rows, total_buy, total_sell, profit = self.db.report(date_from, date_to)
        self.buy_total.value.text = f"{total_buy:,.2f} DA"
        self.sell_total.value.text = f"{total_sell:,.2f} DA"
        self.profit_total.value.text = f"{profit:,.2f} DA"
        self.list_box.clear_widgets()
        for row in rows:
            self.list_box.add_widget(TransactionCard(row, None))


class GoldMobileApp(App):
    title = "Gestion Or Mobile"

    def build(self):
        Window.clearcolor = PAPER
        db_path = Path(self.user_data_dir) / "bijouterie_or_mobile.sqlite3"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = Database(db_path)
        manager = ScreenManager()
        manager.add_widget(LoginScreen(name="login"))
        manager.add_widget(TransactionsScreen(name="transactions"))
        manager.add_widget(ClientsScreen(name="clients"))
        manager.add_widget(ReportScreen(name="report"))
        return manager


if __name__ == "__main__":
    GoldMobileApp().run()
