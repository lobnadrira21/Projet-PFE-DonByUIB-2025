import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { AuthService } from 'app/services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(private router: Router, private auth:AuthService) {}

   canActivate(route: ActivatedRouteSnapshot, _state: RouterStateSnapshot): boolean | UrlTree {
    const token = this.auth.getToken();
    if (!token) return this.router.parseUrl('/login');

    const expected = route.data['role'] as string;
    const role = this.auth.getRole();

    if (role === expected) return true;

    // Logged-in but wrong route → send to their own dashboard
    const target =
      role === 'admin'       ? '/dashboard' :
      role === 'association' ? '/dashboard-association' :
      role === 'donator'     ? '/dashboard-donator' :
                               '/client';
    return this.router.parseUrl(target);
  }
}
