"""Page Objects для онбординга клиента."""

from .name_page import NamePage
from .birth_date_page import BirthDatePage
from .gender_page import GenderPage
from .height_page import HeightPage
from .weight_page import WeightPage
from .fitness_goal_page import FitnessGoalPage
from .workout_experience_page import WorkoutExperiencePage
from .workout_frequency_page import WorkoutFrequencyPage
from .onboarding_complete_page import OnboardingCompletePage

__all__ = ["NamePage", "BirthDatePage", "GenderPage", "HeightPage", "WeightPage", "FitnessGoalPage", "WorkoutExperiencePage", "WorkoutFrequencyPage", "OnboardingCompletePage"]
