"""
FREK v2 — NODE 01 · EXTRACTION
================================
Le signal audio brut entre dans FREK. En moins de 3 secondes, 
6 algorithmes d'analyse fréquentielle extraient la carte d'identité 
sonore complète de l'œuvre.

Output: Vecteur 528 dimensions (~2.1 KB)
- FFT: 512 bandes (20Hz–20kHz)
- RMS: 1 valeur énergétique
- ZCR: 1 valeur texturale
- MFCC: 13 coefficients perceptuels
- Centroïde: 1 valeur de brillance
- Flux: 1 valeur de mouvement
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional
import io


@dataclass
class ExtractionResult:
    """Résultat de l'extraction NODE 01"""
    fft_bands: np.ndarray  # 512 float32
    rms: float
    zcr: float
    mfcc: np.ndarray  # 13 float32
    centroid: float
    flux: float
    duration: float
    sample_rate: int
    
    @property
    def vector_528d(self) -> np.ndarray:
        """Vecteur complet 528 dimensions pour pgvector
        512 FFT + 1 RMS + 1 ZCR + 12 MFCC + 1 Centroid + 1 Flux = 528
        """
        return np.concatenate([
            self.fft_bands,  # 512
            [self.rms],  # 1
            [self.zcr],  # 1
            self.mfcc[:12],  # 12 (on garde les 12 premiers coefficients)
            [self.centroid / 20000],  # 1 (normalisé)
            [self.flux],  # 1
        ]).astype(np.float32)
    
    @property
    def size_bytes(self) -> int:
        """Taille approximative en bytes"""
        return len(self.vector_528d) * 4  # float32 = 4 bytes
    
    def to_dict(self) -> dict:
        return {
            "fft_bands": self.fft_bands.tolist(),
            "rms": round(self.rms, 6),
            "zcr": round(self.zcr, 6),
            "mfcc": self.mfcc.tolist(),
            "centroid": round(self.centroid, 2),
            "flux": round(self.flux, 6),
            "duration": round(self.duration, 2),
            "sample_rate": self.sample_rate,
            "vector_dimensions": len(self.vector_528d),
            "size_kb": round(self.size_bytes / 1024, 2),
        }


class Node01Extraction:
    """
    Pipeline d'extraction FREK — 6 algorithmes simultanés
    
    INPUT: Signal brut (Audio PCM, 16–192 kHz, tout format)
    OUTPUT: Vecteur 528D (~2.1 KB)
    """
    
    FFT_BANDS = 512
    MFCC_COEFFS = 13
    TARGET_SR = 44100
    
    def __init__(self):
        self._librosa = None
    
    def _get_librosa(self):
        """Lazy import de librosa (lourd)"""
        if self._librosa is None:
            import librosa
            self._librosa = librosa
        return self._librosa
    
    async def extract_from_file(self, file_path: str) -> ExtractionResult:
        """Extraction depuis un fichier audio"""
        librosa = self._get_librosa()
        
        # Charger l'audio
        y, sr = librosa.load(file_path, sr=self.TARGET_SR, mono=True)
        return self._extract_features(y, sr)
    
    async def extract_from_bytes(self, audio_bytes: bytes, file_ext: str = "wav") -> ExtractionResult:
        """Extraction depuis des bytes audio"""
        librosa = self._get_librosa()
        import soundfile as sf
        
        # Charger depuis bytes
        audio_io = io.BytesIO(audio_bytes)
        y, sr = sf.read(audio_io)
        
        # Convertir en mono si nécessaire
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)
        
        # Resampler si nécessaire
        if sr != self.TARGET_SR:
            y = librosa.resample(y, orig_sr=sr, target_sr=self.TARGET_SR)
            sr = self.TARGET_SR
        
        return self._extract_features(y, sr)
    
    def _extract_features(self, y: np.ndarray, sr: int) -> ExtractionResult:
        """Pipeline d'extraction des 6 features"""
        librosa = self._get_librosa()
        
        duration = len(y) / sr
        
        # 1. FFT — 512 bandes spectrales (20Hz–20kHz)
        fft_result = np.abs(librosa.stft(y, n_fft=1024, hop_length=512))
        # Moyenne sur le temps, puis réduction à 512 bandes
        fft_mean = np.mean(fft_result, axis=1)
        # Interpoler à exactement 512 bandes
        fft_bands = np.interp(
            np.linspace(0, len(fft_mean) - 1, self.FFT_BANDS),
            np.arange(len(fft_mean)),
            fft_mean
        ).astype(np.float32)
        # Normaliser
        fft_bands = fft_bands / (np.max(fft_bands) + 1e-10)
        
        # 2. RMS — Énergie moyenne
        rms = float(np.sqrt(np.mean(y ** 2)))
        
        # 3. ZCR — Taux de passage par zéro
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        
        # 4. MFCC — 13 coefficients perceptuels
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.MFCC_COEFFS)
        mfcc_mean = np.mean(mfcc, axis=1).astype(np.float32)
        # Normaliser
        mfcc_mean = mfcc_mean / (np.max(np.abs(mfcc_mean)) + 1e-10)
        
        # 5. Centroïde spectral — Centre de gravité fréquentiel
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        centroid_val = float(np.mean(centroid))
        
        # 6. Flux spectral — Variation dans le temps
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        flux = float(np.mean(np.diff(onset_env) ** 2))
        flux = min(flux, 1.0)  # Normaliser
        
        return ExtractionResult(
            fft_bands=fft_bands,
            rms=rms,
            zcr=zcr,
            mfcc=mfcc_mean,
            centroid=centroid_val,
            flux=flux,
            duration=duration,
            sample_rate=sr,
        )


# Instance globale
node01 = Node01Extraction()
