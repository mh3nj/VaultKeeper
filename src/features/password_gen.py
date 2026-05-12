"""
password_gen.py - Advanced password generator
Better than Bitwarden with multiple modes
Supports up to 4096 characters for random passwords
"""

import secrets
import string
from typing import List, Dict

class PasswordGenerator:
    """Generate cryptographically strong passwords"""
    
    # Consonants and vowels for pronounceable passwords
    CONSONANTS = "bcdfghjklmnpqrstvwxyz"
    VOWELS = "aeiou"
    
    # EFF word list (simplified)
    DICEWARE_WORDS = [
        "abacus", "abdomen", "ability", "able", "above", "accept", "accident",
        "account", "achieve", "acoustic", "acquire", "across", "actress",
        "actual", "adapt", "addict", "address", "adjust", "admit", "adult",
        "advance", "advice", "aerobic", "affair", "afford", "afraid", "africa",
        "after", "again", "agency", "agent", "agree", "ahead", "aim",
        "airport", "alarm", "album", "alcohol", "alert", "alien", "all",
        "alley", "allow", "almost", "alone", "alpha", "already", "also",
        "alter", "always", "amazing", "among", "amount", "amuse", "angel",
        "anger", "angle", "angry", "animal", "ankle", "announce", "annual",
        "another", "answer", "antenna", "antique", "anxiety", "any", "apart",
        "apology", "appear", "apple", "approve", "april", "arch", "arctic",
        "area", "arena", "argue", "arm", "army", "around", "arrange",
        "arrest", "arrive", "arrow", "art", "article", "artist", "as",
        "ash", "aside", "ask", "asleep", "aspect", "assault", "asset",
        "assist", "assume", "asthma", "athlete", "atom", "attack", "attend",
        "attitude", "attract", "auction", "audit", "august", "aunt", "author",
        "auto", "autumn", "average", "avocado", "avoid", "awake", "aware",
        "away", "awesome", "awful", "awkward", "axis", "baby", "back",
        "bacon", "bad", "bag", "balance", "ball", "banana", "band",
        "bank", "bar", "bare", "bark", "base", "basic", "basket",
        "bat", "bath", "battle", "bay", "beach", "bean", "bear",
        "beat", "beautiful", "become", "bed", "bee", "beef", "before",
        "begin", "behave", "behind", "believe", "bell", "belong", "below",
        "belt", "bench", "bend", "benefit", "best", "better", "between",
        "beyond", "bicycle", "bid", "big", "bike", "bill", "bird",
        "birth", "bit", "bite", "black", "blade", "blame", "blank"
    ]
    
    # Character sets
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @classmethod
    def generate_random(cls, length: int = 16, use_upper: bool = True,
                        use_lower: bool = True, use_digits: bool = True,
                        use_symbols: bool = True, avoid_ambiguous: bool = True) -> str:
        """Generate random password - EXACT length, supports up to 4096 characters"""
        # Validate length
        if length < 1:
            raise ValueError("Password length must be at least 1")
        if length > 4096:
            raise ValueError("Password length cannot exceed 4096")
        
        # Build character pool
        pool = ""
        if use_lower:
            pool += cls.LOWERCASE
        if use_upper:
            pool += cls.UPPERCASE
        if use_digits:
            pool += cls.DIGITS
        if use_symbols:
            pool += cls.SYMBOLS
        
        # Remove ambiguous characters if requested
        if avoid_ambiguous:
            ambiguous = "il1Lo0O"
            for char in ambiguous:
                pool = pool.replace(char, '')
        
        # Ensure at least one character set is selected
        if not pool:
            pool = cls.LOWERCASE + cls.UPPERCASE + cls.DIGITS
        
        # Generate EXACT length - use list comprehension for speed
        # This guarantees exactly 'length' characters
        result_chars = [secrets.choice(pool) for _ in range(length)]
        return ''.join(result_chars)
    
    @classmethod
    def generate_pronounceable(cls, length: int = 12) -> str:
        """Generate pronounceable password (easier to remember)"""
        if length < 4:
            raise ValueError("Length must be at least 4")
        if length > 30:
            raise ValueError("Length cannot exceed 30")
        
        password = []
        for i in range(length):
            if i % 2 == 0:
                password.append(secrets.choice(cls.CONSONANTS))
            else:
                password.append(secrets.choice(cls.VOWELS))
        
        result = ''.join(password)
        
        # Add a random number at the end sometimes
        if secrets.randbelow(3) == 0:  # 33% chance
            result += str(secrets.randbelow(10))
        
        # Capitalize first letter
        return result.capitalize()
    
    @classmethod
    def generate_diceware(cls, word_count: int = 6, separator: str = " ") -> str:
        """Generate diceware passphrase using EFF word list"""
        if word_count < 3:
            raise ValueError("Word count must be at least 3")
        if word_count > 12:
            raise ValueError("Word count cannot exceed 12")
        
        words = [secrets.choice(cls.DICEWARE_WORDS) for _ in range(word_count)]
        return separator.join(words)
    
    @classmethod
    def generate_pin(cls, length: int = 6) -> str:
        """Generate numeric PIN"""
        if length < 4:
            raise ValueError("PIN length must be at least 4")
        if length > 12:
            raise ValueError("PIN length cannot exceed 12")
        
        return ''.join(str(secrets.randbelow(10)) for _ in range(length))
    
    @classmethod
    def generate_apple_style(cls) -> str:
        """Generate Apple-style password (noun-verb-number)"""
        nouns = ["grape", "apple", "storm", "cloud", "river", "mountain", 
                 "forest", "ocean", "thunder", "lightning", "butterfly", 
                 "dragon", "phoenix", "eagle", "tiger", "lion", "wolf"]
        verbs = ["jump", "run", "fly", "swim", "climb", "dance", "sing", 
                 "write", "read", "dream", "think", "create", "build", 
                 "explore", "discover", "imagine"]
        numbers = secrets.randbelow(1000)
        
        noun = secrets.choice(nouns)
        verb = secrets.choice(verbs)
        return f"{noun}-{verb}-{numbers:03d}"
    
    @classmethod
    def check_strength(cls, password: str) -> Dict:
        """Check password strength (0-4) returning full details"""
        score = 0
        feedback = []
        
        # Length
        if len(password) >= 20:
            score += 2
        elif len(password) >= 12:
            score += 1
        else:
            feedback.append("Password is too short")
        
        # Character variety
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in cls.SYMBOLS for c in password)
        
        variety = sum([has_lower, has_upper, has_digit, has_symbol])
        score += variety - 1 if variety > 1 else 0
        
        if variety < 3:
            feedback.append("Add more character types")
        
        # Rating
        if score >= 4:
            rating = "Excellent"
        elif score >= 3:
            rating = "Good"
        elif score >= 2:
            rating = "Fair"
        else:
            rating = "Weak"
        
        return {
            'score': min(score, 4),
            'rating': rating,
            'feedback': feedback,
            'length': len(password),
            'has_upper': has_upper,
            'has_lower': has_lower,
            'has_digit': has_digit,
            'has_symbol': has_symbol
        }
