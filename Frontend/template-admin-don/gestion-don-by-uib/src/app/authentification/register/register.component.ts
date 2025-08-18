import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RecaptchaModule } from 'ng-recaptcha';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { HttpClient, HttpClientModule } from '@angular/common/http';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RecaptchaModule,
    RouterModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    MatCheckboxModule,
    HttpClientModule
  ],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit, OnDestroy {
  // ─── original form fields ─────────────────────────────────────────
  email = '';
  password = '';
  confirmPassword = '';
  nom_complet = '';
  telephone = '';
  role = 'donator';
  errorMessage = '';
  captchaImage = '';
  captchaAnswer = '';
  userCaptchaInput = '';
  hideTelError = false;
  hidePwdError = false;

  // ─── flow de vérification ────────────────────────────────────────
  faceVerified = false;
  sessionId: string | null = null;

  // ─── CIN modal fields ────────────────────────────────────────────
  showCinModal = false;
  cinFile!: File;
  isCinVerifying = false;
  cinMessage = '';
  cinOk = false;

  // ─── Selfie modal & caméra ───────────────────────────────────────
  showSelfieModal = false;
  isSelfieVerifying = false;
  selfieMessage = '';
  selfieOk = false;
  selfieScore: number | null = null;
  selfieThreshold: number | null = null;

  @ViewChild('videoEl') videoEl!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasEl') canvasEl!: ElementRef<HTMLCanvasElement>;
  private mediaStream: MediaStream | null = null;
  cameraReady = false;
  cameraError = '';
  capturedDataUrl: string | null = null;
  private capturedBlob: Blob | null = null;

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // fetch captcha from back-end
    this.http.get<any>('http://127.0.0.1:5000/get-captcha-image').subscribe({
      next: data => {
        this.captchaImage = data.captcha_image;
        this.captchaAnswer = data.captcha_text;
      },
      error: err => {
        console.error('Erreur captcha', err);
      }
    });
  }

  ngOnDestroy(): void {
    this.stopCamera();
  }

  // ── Ouvrir / fermer modals ───────────────────────────────────────
  openCinModal() {
    this.errorMessage = '';
    this.cinMessage = '';
    this.cinOk = false;
    this.showCinModal = true;
  }
  cancelCinModal() {
    this.showCinModal = false;
    this.cinFile = undefined as any;
    this.cinMessage = '';
    this.cinOk = false;
  }

  private openSelfieAfterCin() {
    this.showSelfieModal = true;
    setTimeout(() => this.startCamera(), 0);
  }
  cancelSelfieModal() {
    this.showSelfieModal = false;
    this.stopCamera();
    this.selfieMessage = '';
    this.selfieOk = false;
    this.selfieScore = null;
    this.selfieThreshold = null;
    this.capturedDataUrl = null;
    this.capturedBlob = null;
  }

  // ── file handler (CIN) ───────────────────────────────────────────
  onCinFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length) {
      this.cinFile = input.files[0];
      this.cinMessage = '';
    }
  }

  // ── Camera helpers ───────────────────────────────────────────────
  async startCamera() {
    this.cameraError = '';
    this.cameraReady = false;
    this.capturedDataUrl = null;
    this.capturedBlob = null;

    try {
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: { ideal: 'user' },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      const video = this.videoEl?.nativeElement;
      if (video) {
        video.srcObject = this.mediaStream;
        await video.play().catch(() => {});
        await this.waitForVideoFrame(video); // ✅ ensure we have an actual frame
        this.cameraReady = true;
      }
    } catch (err: any) {
      console.error('Camera error', err);
      this.cameraError =
        'Impossible d’accéder à la caméra. Vérifiez les permissions ou utilisez HTTPS.';
      this.cameraReady = false;
    }
  }
private waitForVideoFrame(video: HTMLVideoElement): Promise<void> {
  return new Promise((resolve) => {
    // Avoid "in" narrowing — check via typeof on an augmented type
    const v = video as HTMLVideoElement & {
      requestVideoFrameCallback?: (cb: () => void) => number;
    };

    if (typeof v.requestVideoFrameCallback === 'function') {
      v.requestVideoFrameCallback(() => resolve());
      return;
    }

    // HAVE_CURRENT_DATA = 2
    if (video.readyState >= 2) {
      requestAnimationFrame(() => resolve());
      return;
    }

    const onLoaded = () => {
      video.removeEventListener('loadeddata', onLoaded as EventListener);
      resolve();
    };
    video.addEventListener('loadeddata', onLoaded as EventListener, { once: true });
  });
}


  stopCamera() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    this.cameraReady = false;
  }

  async captureSelfie() {
    const video = this.videoEl?.nativeElement;
    const canvas = this.canvasEl?.nativeElement;
    if (!video || !canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // ✅ Try ImageCapture first (more reliable than drawing a possibly empty <video>)
    const track = this.mediaStream?.getVideoTracks()[0];
    let frameW = 0, frameH = 0;
    let drew = false;

    if (track && (window as any).ImageCapture) {
      try {
        const imageCapture = new (window as any).ImageCapture(track);
        const bitmap: ImageBitmap = await imageCapture.grabFrame();
        frameW = bitmap.width;
        frameH = bitmap.height;
        const side = Math.min(frameW, frameH);
        const sx = (frameW - side) / 2;
        const sy = (frameH - side) / 2;

        canvas.width = side;
        canvas.height = side;
        ctx.drawImage(bitmap, sx, sy, side, side, 0, 0, side, side);
        drew = true;
      } catch {
        // fall back to video frame
      }
    }

    // Fallback: ensure a real video frame is available, then draw
    if (!drew) {
      await this.waitForVideoFrame(video);
      frameW = video.videoWidth;
      frameH = video.videoHeight;

      if (!frameW || !frameH) {
        this.selfieMessage = 'La caméra n’a pas encore fourni d’image. Réessayez.';
        return;
      }

      const side = Math.min(frameW, frameH);
      const sx = (frameW - side) / 2;
      const sy = (frameH - side) / 2;

      canvas.width = side;
      canvas.height = side;
      ctx.drawImage(video, sx, sy, side, side, 0, 0, side, side);
    }

    // Convert canvas → Blob → preview URL, then stop camera
    await new Promise<void>((resolve) => {
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            this.selfieMessage = 'Capture échouée. Réessayez.';
            resolve();
            return;
          }
          this.capturedBlob = blob;
          this.capturedDataUrl = URL.createObjectURL(blob);
          resolve();
        },
        'image/jpeg',
        0.92
      );
    });

    this.stopCamera();
  }

  retakeSelfie() {
    this.capturedDataUrl = null;
    this.capturedBlob = null;
    this.startCamera();
  }

  // ── Step 1: Vérifier CIN → récup session_id ─────────────────────
  verifyCin() {
    if (!this.cinFile) {
      this.cinMessage = 'Veuillez uploader votre CIN.';
      this.cinOk = false;
      return;
    }

    this.isCinVerifying = true;
    this.authService.verifyCin(this.cinFile).subscribe({
      next: (res) => {
        this.isCinVerifying = false;
        if (res?.ok && res?.session_id) {
          this.sessionId = res.session_id;
          this.cinOk = true;
          this.cinMessage = 'CIN validée. Passons au selfie.';
          this.showCinModal = false;
          this.openSelfieAfterCin();
        } else {
          this.cinOk = false;
          this.cinMessage = 'Réponse inattendue du serveur.';
        }
      },
      error: (err) => {
        this.isCinVerifying = false;
        this.cinOk = false;

        if (err.status === 422) {
          const reason = err.error?.reason || 'Visage non détecté.';
          this.cinMessage = `CIN reconnue mais ${reason}. Réessayez avec une image plus nette.`;
        } else if (err.status === 400) {
          this.cinMessage = 'CIN invalide (document ou drapeau non reconnus).';
        } else {
          this.cinMessage = err.error?.message || 'La vérification de la CIN a échoué.';
        }
      }
    });
  }

  // ── Step 2: Vérifier Selfie contre session_id ───────────────────
  verifySelfie() {
    if (!this.capturedBlob) {
      this.selfieMessage = 'Veuillez d’abord prendre une photo.';
      this.selfieOk = false;
      return;
    }
    if (!this.sessionId) {
      this.selfieMessage = 'Session de vérification introuvable. Recommencez la vérification CIN.';
      this.selfieOk = false;
      return;
    }

    this.isSelfieVerifying = true;

    // on fabrique un File à partir du Blob pour FormData
    const selfieFile = new File([this.capturedBlob], 'selfie.jpg', { type: 'image/jpeg' });

    this.authService.verifyFace(selfieFile, this.sessionId).subscribe({
      next: (res) => {
        this.isSelfieVerifying = false;
        this.selfieScore = res?.score ?? null;
        this.selfieThreshold = res?.threshold ?? null;

        if (res?.ok && res?.match === true) {
          this.selfieOk = true;
          this.selfieMessage = 'Vérification faciale réussie ✅';
          this.faceVerified = true;
          this.showSelfieModal = false;
          this.register();
        } else {
          this.selfieOk = false;
          this.faceVerified = false;
          this.selfieMessage = 'Le selfie ne correspond pas à la CIN. Réessayez.';
        }
      },
      error: (err) => {
        this.isSelfieVerifying = false;
        this.selfieOk = false;
        this.faceVerified = false;

        if (err.status === 422) {
          const reason = err.error?.reason || 'Visage non détecté.';
          this.selfieMessage = `Selfie non exploitable : ${reason}.`;
        } else if (err.status === 404 && err.error?.reason === 'unknown_session') {
          this.selfieMessage = 'Session expirée ou inconnue. Recommencez la vérification CIN.';
        } else {
          this.selfieMessage = err.error?.message || 'La vérification du selfie a échoué.';
        }
      }
    });
  }

  // ── Register (garde faceVerified) ────────────────────────────────
  register() {
    this.errorMessage = '';

    if (!this.faceVerified) {
      this.errorMessage = 'Veuillez d’abord vérifier votre CIN puis votre selfie.';
      return;
    }

    if (!this.email || !this.password || !this.nom_complet || !this.telephone) {
      this.errorMessage = 'Tous les champs sont requis.';
      return;
    }
    if (!this.isValidNomComplet()) {
      this.errorMessage = 'Le nom complet doit contenir au maximum 40 caractères.';
      return;
    }
    if (!this.isValidEmail()) {
      this.errorMessage = "L'adresse email n'est pas valide.";
      return;
    }
    if (!this.isValidTelephone()) {
      this.errorMessage = 'Le numéro de téléphone doit comporter exactement 8 chiffres.';
      return;
    }
    if (!this.isStrongPassword()) {
      this.errorMessage = 'Le mot de passe doit contenir une majuscule, un chiffre et un caractère spécial.';
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Les mots de passe ne correspondent pas.';
      return;
    }
    if (this.userCaptchaInput.trim().toUpperCase() !== this.captchaAnswer.trim().toUpperCase()) {
      this.errorMessage = 'Le code captcha est incorrect.';
      return;
    }

    const userData = {
      email: this.email,
      password: this.password,
      nom_complet: this.nom_complet,
      telephone: this.telephone,
      role: this.role
    };

    this.authService.register(userData).subscribe({
      next: response => {
        if (response.access_token) {
          this.authService.saveToken(
            response.access_token,
            response.role,
            response.username
          );
        }
        if (response.role === 'donator') {
          this.router.navigate(['/dashboard-donator']);
        } else {
          this.router.navigate(['/login']);
        }
      },
      error: error => {
        console.error('Registration failed:', error);
        this.errorMessage = error.error?.error || 'Une erreur est survenue.';
      }
    });
  }

  // ── divers helpers ───────────────────────────────────────────────
  goToHome() { this.router.navigate(['/']); }
  isValidNomComplet(): boolean {
    const regex = /^[A-Za-zÀ-ÿ\s\-]{1,40}$/;
    return regex.test(this.nom_complet);
  }
  isValidEmail(): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(this.email);
  }
  isValidTelephone(): boolean {
    const phoneRegex = /^\d{8}$/;
    return phoneRegex.test(this.telephone);
  }
  isStrongPassword(): boolean {
    const regex = /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$/;
    return regex.test(this.password);
  }
  refreshCaptcha() { this.ngOnInit(); }
}
