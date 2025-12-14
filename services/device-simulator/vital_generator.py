"""Realistic vital signs generator with patterns"""
import random
import math
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class EpisodeType(Enum):
    """Types of medical episodes"""
    NONE = "none"
    FEVER_SPIKE = "fever_spike"
    HYPOXIA = "hypoxia"
    TACHYCARDIA = "tachycardia"


@dataclass
class PatientBaseline:
    """Baseline vital signs for a patient"""
    hr_baseline: float  # Heart rate baseline (bpm)
    spo2_baseline: float  # Oxygen saturation baseline (%)
    temp_baseline: float  # Temperature baseline (°C)
    hr_min: float
    hr_max: float
    spo2_min: float
    temp_min: float
    temp_max: float


@dataclass
class EpisodeState:
    """State of an ongoing episode"""
    episode_type: EpisodeType
    start_time: float
    duration: float  # Duration in seconds
    severity: float  # 0.0 to 1.0


class VitalGenerator:
    """Generates realistic vital signs with patterns"""
    
    def __init__(self, baseline: PatientBaseline, episode_rate: float = 0.05):
        """
        Initialize generator with patient baseline
        
        Args:
            baseline: Patient baseline vital signs
            episode_rate: Probability of episode per interval (0.0 to 1.0)
        """
        self.baseline = baseline
        self.episode_rate = episode_rate
        self.current_episode: Optional[EpisodeState] = None
        self.time_since_start = 0.0
        
        # Episode parameters
        self.episode_duration_range = (30, 300)  # 30 seconds to 5 minutes
        self.episode_severity_range = (0.3, 0.9)  # Mild to severe
    
    def generate(self, elapsed_time: float) -> Tuple[float, float, float, EpisodeType]:
        """
        Generate vital signs for current time
        
        Args:
            elapsed_time: Time elapsed since start (seconds)
        
        Returns:
            Tuple of (heart_rate, spo2, temperature, episode_type)
        """
        self.time_since_start = elapsed_time
        
        # Check if we should start a new episode
        if self.current_episode is None:
            if random.random() < self.episode_rate:
                self._start_episode()
        
        # Check if current episode should end
        if self.current_episode:
            episode_elapsed = elapsed_time - self.current_episode.start_time
            if episode_elapsed >= self.current_episode.duration:
                self.current_episode = None
        
        # Generate vitals based on current state
        if self.current_episode:
            hr, spo2, temp = self._generate_with_episode()
            episode_type = self.current_episode.episode_type
        else:
            hr, spo2, temp = self._generate_normal()
            episode_type = EpisodeType.NONE
        
        return hr, spo2, temp, episode_type
    
    def _start_episode(self):
        """Start a new medical episode"""
        episode_types = [
            EpisodeType.FEVER_SPIKE,
            EpisodeType.HYPOXIA,
            EpisodeType.TACHYCARDIA
        ]
        episode_type = random.choice(episode_types)
        duration = random.uniform(*self.episode_duration_range)
        severity = random.uniform(*self.episode_severity_range)
        
        self.current_episode = EpisodeState(
            episode_type=episode_type,
            start_time=self.time_since_start,
            duration=duration,
            severity=severity
        )
        
        logger.info(
            f"Started {episode_type.value} episode: "
            f"duration={duration:.1f}s, severity={severity:.2f}"
        )
    
    def _generate_normal(self) -> Tuple[float, float, float]:
        """Generate normal vital signs with small noise"""
        # Heart rate: baseline ± 5 bpm with small random variation
        hr_noise = random.gauss(0, 2.0)  # Gaussian noise, std dev 2 bpm
        hr = self.baseline.hr_baseline + hr_noise
        hr = max(self.baseline.hr_min, min(self.baseline.hr_max, hr))
        
        # SpO2: baseline ± 1% with small random variation
        spo2_noise = random.gauss(0, 0.5)  # Gaussian noise, std dev 0.5%
        spo2 = self.baseline.spo2_baseline + spo2_noise
        spo2 = max(self.baseline.spo2_min, min(100.0, spo2))
        
        # Temperature: baseline ± 0.2°C with small random variation
        temp_noise = random.gauss(0, 0.1)  # Gaussian noise, std dev 0.1°C
        temp = self.baseline.temp_baseline + temp_noise
        temp = max(self.baseline.temp_min, min(self.baseline.temp_max, temp))
        
        return round(hr, 1), round(spo2, 1), round(temp, 2)
    
    def _generate_with_episode(self) -> Tuple[float, float, float]:
        """Generate vital signs during an episode"""
        episode = self.current_episode
        episode_elapsed = self.time_since_start - episode.start_time
        progress = episode_elapsed / episode.duration  # 0.0 to 1.0
        
        # Create a bell curve for episode intensity (peaks in middle)
        intensity = math.sin(progress * math.pi) * episode.severity
        
        if episode.episode_type == EpisodeType.FEVER_SPIKE:
            # Fever: temperature rises, heart rate increases slightly
            temp_increase = intensity * 2.5  # Up to 2.5°C increase
            hr_increase = intensity * 15  # Up to 15 bpm increase
            
            temp = self.baseline.temp_baseline + temp_increase
            temp = min(temp, self.baseline.temp_max + 1.0)  # Can exceed normal max slightly
            
            hr = self.baseline.hr_baseline + hr_increase
            hr = min(hr, self.baseline.hr_max + 20)  # Can exceed normal max
            
            spo2 = self.baseline.spo2_baseline - intensity * 2  # Slight decrease
            spo2 = max(spo2, self.baseline.spo2_min - 1.0)
        
        elif episode.episode_type == EpisodeType.HYPOXIA:
            # Hypoxia: SpO2 drops significantly, heart rate increases
            spo2_drop = intensity * 10  # Up to 10% drop
            hr_increase = intensity * 20  # Up to 20 bpm increase
            
            spo2 = self.baseline.spo2_baseline - spo2_drop
            spo2 = max(spo2, self.baseline.spo2_min - 5.0)  # Can drop below normal min
            
            hr = self.baseline.hr_baseline + hr_increase
            hr = min(hr, self.baseline.hr_max + 25)
            
            temp = self.baseline.temp_baseline + intensity * 0.5  # Slight increase
            temp = min(temp, self.baseline.temp_max)
        
        elif episode.episode_type == EpisodeType.TACHYCARDIA:
            # Tachycardia: heart rate spikes, SpO2 may drop slightly
            hr_increase = intensity * 40  # Up to 40 bpm increase
            spo2_drop = intensity * 3  # Up to 3% drop
            
            hr = self.baseline.hr_baseline + hr_increase
            hr = min(hr, self.baseline.hr_max + 50)  # Can exceed normal max significantly
            
            spo2 = self.baseline.spo2_baseline - spo2_drop
            spo2 = max(spo2, self.baseline.spo2_min - 2.0)
            
            temp = self.baseline.temp_baseline + intensity * 0.3
            temp = min(temp, self.baseline.temp_max)
        
        else:
            # Fallback to normal
            return self._generate_normal()
        
        # Add small noise even during episodes
        hr += random.gauss(0, 1.5)
        spo2 += random.gauss(0, 0.3)
        temp += random.gauss(0, 0.05)
        
        return round(hr, 1), round(spo2, 1), round(temp, 2)

