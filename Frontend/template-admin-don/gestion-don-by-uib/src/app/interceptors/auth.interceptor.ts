import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpInterceptor,
  HttpHandler,
  HttpRequest,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { AuthService } from 'app/services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private router: Router, private authService: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = localStorage.getItem('token');

    // ✅ Ajouter l'en-tête Authorization si le token existe
    const authReq = token
      ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : req;

    return next.handle(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        // ✅ Vérifie uniquement les erreurs 401
        if (error.status === 401) {
          // ❌ Ne pas rediriger pour certaines routes (erreurs attendues)
          const excludedEndpoints = [
            '/modify-profile-donateur',
            '/reset-password',
            '/participate',
            '/add-comment',
            '/like-publication',
            '/get-profile-donator'
          ];

          const shouldRedirect = !excludedEndpoints.some(endpoint =>
            req.url.includes(endpoint)
          );

          if (shouldRedirect) {
            this.authService.logout();
            this.router.navigate(['/login']);
          }
        }

        return throwError(() => error);
      })
    );
  }
}
