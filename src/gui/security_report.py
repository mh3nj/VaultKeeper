"""
security_report.py - Security Report Dashboard with real vault data
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class SecurityReportDialog:
    """Security Report Dashboard using real vault data"""
    
    def __init__(self, parent, dark_mode=False, vault_manager=None):
        self.parent = parent
        self.dark_mode = dark_mode
        self.vault = vault_manager
        self.report_data = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Security Report - VaultKeeper")
        self.dialog.geometry("900x750")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Generate report from real data
        self.generate_report()
        
        # Setup UI
        self.setup_ui()
    
    def get_colors(self):
        if self.dark_mode:
            return {"bg": "#1e1e1e", "fg": "#ffffff", "entry_bg": "#3d3d3d", "entry_fg": "#ffffff",
                    "button_bg": "#3d3d3d", "button_fg": "#ffffff", "accent": "#3b82f6",
                    "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444", "border": "#4a4a4a"}
        else:
            return {"bg": "#f5f5f5", "fg": "#000000", "entry_bg": "#ffffff", "entry_fg": "#000000",
                    "button_bg": "#e5e7eb", "button_fg": "#000000", "accent": "#3b82f6",
                    "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444", "border": "#d1d5db"}
    
    def generate_report(self):
        """Generate report from ACTUAL vault data"""
        entries = []
        if self.vault and self.vault.db:
            try:
                entries = self.vault.db.get_all_entries()
                print(f"📊 Generating security report for {len(entries)} entries...")
            except Exception as e:
                print(f"Error getting entries: {e}")
        
        # Check for weak passwords (simple heuristics)
        weak_passwords = []
        known_weak = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome']
        
        for e in entries:
            pwd = e.get('password', '')
            if not pwd:
                continue
            
            reasons = []
            if len(pwd) < 8:
                reasons.append("Too short")
            if pwd.lower() in known_weak:
                reasons.append("Common password")
            if not any(c.isupper() for c in pwd):
                reasons.append("No uppercase")
            if not any(c.islower() for c in pwd):
                reasons.append("No lowercase")
            if not any(c.isdigit() for c in pwd):
                reasons.append("No numbers")
            
            if reasons:
                weak_passwords.append({
                    'title': e.get('title', 'Unknown'),
                    'username': e.get('username', ''),
                    'strength': 1,
                    'reason': ', '.join(reasons)
                })
        
        # Check for duplicate passwords
        password_count = {}
        for e in entries:
            pwd = e.get('password', '')
            if pwd:
                password_count[pwd] = password_count.get(pwd, 0) + 1
        
        duplicate_passwords = []
        for pwd, count in password_count.items():
            if count > 1:
                duplicate_passwords.append({
                    'password': pwd[:20] + "..." if len(pwd) > 20 else pwd,
                    'count': count,
                    'entries': [e.get('title', '') for e in entries if e.get('password') == pwd][:5]
                })
        
        # Calculate security score
        total = len(entries)
        weak_count = len(weak_passwords)
        duplicate_count = len(duplicate_passwords)
        
        score = 100
        issues = []
        
        if weak_count > 0:
            score -= min(40, weak_count * 5)
            issues.append(f"{weak_count} weak passwords found")
        if duplicate_count > 0:
            score -= min(30, duplicate_count * 8)
            issues.append(f"Passwords reused {duplicate_count} times")
        if total == 0:
            score = 100
        
        self.report_data = {
            'total_entries': total,
            'weak_passwords': weak_passwords,
            'duplicate_passwords': duplicate_passwords,
            'expiring_passwords': [],
            'reused_passwords': duplicate_count,
            'security_score': {
                'score': max(0, score),
                'grade': self._get_grade(max(0, score)),
                'issues': issues if issues else ["No security issues found!"]
            }
        }
    
    def _get_grade(self, score: int) -> str:
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def setup_ui(self):
        colors = self.get_colors()
        self.dialog.configure(bg=colors["bg"])
        
        # Scrollable frame
        canvas = tk.Canvas(self.dialog, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dialog, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors["bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=880)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        main_frame = tk.Frame(scrollable_frame, bg=colors["bg"], padx=25, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header_frame, text="📊 Security Report", font=("Segoe UI", 20, "bold"),
                        bg=colors["bg"], fg=colors["fg"])
        title.pack(side=tk.LEFT)
        
        # Score Card
        score_frame = tk.Frame(main_frame, bg=colors["entry_bg"], relief=tk.RAISED, bd=1)
        score_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.create_score_card(score_frame)
        
        # Stats Cards
        stats_frame = tk.Frame(main_frame, bg=colors["bg"])
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        self.create_stats_cards(stats_frame)
        
        # Weak Passwords Section
        weak_frame = tk.LabelFrame(main_frame, text="⚠️ Weak Passwords", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12, "bold"))
        weak_frame.pack(fill=tk.X, pady=(0, 15))
        self.create_weak_passwords_section(weak_frame)
        
        # Duplicate Passwords Section
        dup_frame = tk.LabelFrame(main_frame, text="🔄 Duplicate Passwords", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12, "bold"))
        dup_frame.pack(fill=tk.X, pady=(0, 15))
        self.create_duplicate_section(dup_frame)
        
        # Recommendations
        rec_frame = tk.LabelFrame(main_frame, text="💡 Recommendations", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12, "bold"))
        rec_frame.pack(fill=tk.X, pady=(0, 15))
        self.create_recommendations(rec_frame)
        
        # Close button
        close_btn = tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                             bg=colors["button_bg"], fg=colors["button_fg"],
                             relief=tk.FLAT, cursor='hand2', padx=30, pady=8)
        close_btn.pack(pady=10)
    
    def create_score_card(self, parent):
        colors = self.get_colors()
        score = self.report_data['security_score']
        
        score_canvas = tk.Canvas(parent, width=120, height=120, bg=colors["entry_bg"], highlightthickness=0)
        score_canvas.pack(side=tk.LEFT, padx=20, pady=20)
        
        if score['score'] >= 80:
            color = colors["success"]
        elif score['score'] >= 60:
            color = colors["warning"]
        else:
            color = colors["danger"]
        
        score_canvas.create_oval(10, 10, 110, 110, outline=color, width=8)
        score_canvas.create_text(60, 50, text=str(score['score']), font=("Segoe UI", 28, "bold"), fill=color)
        score_canvas.create_text(60, 80, text=f"Grade {score['grade']}", font=("Segoe UI", 12), fill=colors["fg"])
        
        info_frame = tk.Frame(parent, bg=colors["entry_bg"])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(info_frame, text="Overall Security Score", font=("Segoe UI", 14, "bold"),
                bg=colors["entry_bg"], fg=colors["fg"]).pack(anchor='w')
        
        tk.Label(info_frame, text=f"Based on {self.report_data['total_entries']} entries",
                font=("Segoe UI", 10), bg=colors["entry_bg"], fg=colors["fg"] if self.dark_mode else '#6b7280'
        ).pack(anchor='w', pady=(5, 10))
        
        for issue in score['issues']:
            tk.Label(info_frame, text=f"• {issue}", font=("Segoe UI", 10),
                    bg=colors["entry_bg"], fg=colors["warning"]).pack(anchor='w', pady=2)
    
    def create_stats_cards(self, parent):
        colors = self.get_colors()
        
        stats = [
            ("Total Entries", self.report_data['total_entries'], "🔐"),
            ("Weak Passwords", len(self.report_data['weak_passwords']), "⚠️"),
            ("Duplicates", len(self.report_data['duplicate_passwords']), "🔄"),
        ]
        
        for label, value, icon in stats:
            card = tk.Frame(parent, bg=colors["entry_bg"], relief=tk.RAISED, bd=1, width=180, height=100)
            card.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)
            card.pack_propagate(False)
            
            tk.Label(card, text=icon, font=("Segoe UI", 24), bg=colors["entry_bg"], fg=colors["accent"]
                    ).pack(pady=(10, 0))
            tk.Label(card, text=str(value), font=("Segoe UI", 20, "bold"),
                    bg=colors["entry_bg"], fg=colors["fg"]).pack()
            tk.Label(card, text=label, font=("Segoe UI", 9),
                    bg=colors["entry_bg"], fg=colors["fg"] if self.dark_mode else '#6b7280').pack()
    
    def create_weak_passwords_section(self, parent):
        colors = self.get_colors()
        
        if not self.report_data['weak_passwords']:
            tk.Label(parent, text="✓ No weak passwords found!", font=("Segoe UI", 11),
                    bg=colors["bg"], fg=colors["success"], pady=10).pack()
            return
        
        tree_frame = tk.Frame(parent, bg=colors["bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Title", "Username", "Reason")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
        
        tree.heading("Title", text="Title")
        tree.heading("Username", text="Username")
        tree.heading("Reason", text="Reason")
        
        tree.column("Title", width=200)
        tree.column("Username", width=180)
        tree.column("Reason", width=200)
        
        for item in self.report_data['weak_passwords']:
            tree.insert("", tk.END, values=(item['title'], item['username'], item['reason']))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    def create_duplicate_section(self, parent):
        colors = self.get_colors()
        
        if not self.report_data['duplicate_passwords']:
            tk.Label(parent, text="✓ No duplicate passwords found!", font=("Segoe UI", 11),
                    bg=colors["bg"], fg=colors["success"], pady=10).pack()
            return
        
        for dup in self.report_data['duplicate_passwords']:
            dup_frame = tk.Frame(parent, bg=colors["entry_bg"], relief=tk.RAISED, bd=1)
            dup_frame.pack(fill=tk.X, padx=10, pady=5)
            
            header = tk.Frame(dup_frame, bg=colors["entry_bg"])
            header.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(header, text=f"Password: {dup['password']}", font=("Courier", 10, "bold"),
                    bg=colors["entry_bg"], fg=colors["warning"]).pack(side=tk.LEFT)
            tk.Label(header, text=f"(used {dup['count']} times)", font=("Segoe UI", 9),
                    bg=colors["entry_bg"], fg=colors["fg"] if self.dark_mode else '#6b7280'
            ).pack(side=tk.LEFT, padx=(10, 0))
            
            entries_frame = tk.Frame(dup_frame, bg=colors["entry_bg"])
            entries_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            
            tk.Label(entries_frame, text="Used in: " + ", ".join(dup['entries']),
                    font=("Segoe UI", 9), bg=colors["entry_bg"], fg=colors["fg"]).pack(anchor='w')
    
    def create_recommendations(self, parent):
        colors = self.get_colors()
        
        recommendations = [
            "🔐 Use unique passwords for every account",
            "📏 Aim for passwords with 16+ characters",
            "🔀 Enable 2FA wherever possible",
            "🔄 Change passwords every 90 days",
            "📋 Use the password generator for strong passwords",
            "🔍 Run security reports regularly",
            "💾 Keep encrypted backups of your vault"
        ]
        
        for rec in recommendations:
            tk.Label(parent, text=rec, font=("Segoe UI", 10),
                    bg=colors["bg"], fg=colors["fg"], anchor='w', padx=15, pady=5).pack(fill=tk.X)
