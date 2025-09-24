import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from 'app/services/auth.service';
import { ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';


@Injectable({
  providedIn: 'root'
})
export class NoAuthGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean | UrlTree {
    const token = this.auth.getToken();
    const url = state.url;

    // Always allow these
    if (url === '/client' || url.startsWith('/reset-password') || url.startsWith('/request-password')) {
      return true;
    }

    const isAuthPages = url.startsWith('/login') || url.startsWith('/register');
    if (!token) return true;

    if (isAuthPages) {
      const role = this.auth.getRole();
      const target =
        role === 'admin'       ? '/dashboard' :
        role === 'association' ? '/dashboard-association' :
        role === 'donator'     ? '/dashboard-donator' :
                                 '/client';
      return this.router.parseUrl(target);
    }
    return true;
  }
}