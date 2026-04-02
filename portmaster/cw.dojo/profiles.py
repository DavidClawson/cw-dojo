"""User profile management for the Morse trainer."""

import json
import os
from progress import KochProgress

PROFILES_FILE = 'profiles.json'


class ProfileManager:
    """Manages multiple user profiles, each with their own Koch progress."""

    def __init__(self, active='Default', profiles=None):
        self.active = active
        self.profiles = profiles or {'Default': {'progress_file': 'koch_progress.json'}}

    def save(self, path=None):
        path = path or PROFILES_FILE
        data = {'active': self.active, 'profiles': self.profiles}
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path=None):
        path = path or PROFILES_FILE
        if not os.path.exists(path):
            # Migrate: if koch_progress.json exists, create default profile for it
            mgr = cls()
            mgr.save(path)
            return mgr
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls(active=data.get('active', 'Default'),
                       profiles=data.get('profiles', {}))
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()

    def profile_names(self):
        return list(self.profiles.keys())

    def progress_file(self, name=None):
        name = name or self.active
        return self.profiles.get(name, {}).get('progress_file', 'koch_progress.json')

    def load_progress(self, name=None):
        return KochProgress.load(self.progress_file(name))

    def create_profile(self, name, starting_level=0):
        safe = name.strip()
        if not safe or safe in self.profiles:
            return False
        fname = f'koch_progress_{safe.lower().replace(" ", "_")}.json'
        self.profiles[safe] = {'progress_file': fname}
        # Create initial progress with the given starting level
        p = KochProgress(level=starting_level)
        p.save(fname)
        self.save()
        return True

    def delete_profile(self, name):
        if name not in self.profiles or len(self.profiles) <= 1:
            return False
        # Remove progress file
        fname = self.profiles[name]['progress_file']
        if os.path.exists(fname):
            os.remove(fname)
        del self.profiles[name]
        if self.active == name:
            self.active = next(iter(self.profiles))
        self.save()
        return True

    def switch_to(self, name, current_progress):
        """Switch active profile. Saves current progress, loads new into current_progress object."""
        if name not in self.profiles:
            return False
        # Save current profile's progress
        current_progress.save(self.progress_file())
        # Switch active
        self.active = name
        self.save()
        # Load new profile's progress into the existing object
        new = KochProgress.load(self.progress_file())
        current_progress.level = new.level
        current_progress.total_correct = new.total_correct
        current_progress.total_attempts = new.total_attempts
        current_progress.level_correct = new.level_correct
        current_progress.level_attempts = new.level_attempts
        current_progress.char_stats = new.char_stats
        return True
