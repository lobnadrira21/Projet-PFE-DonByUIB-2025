import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from 'app/services/auth.service';

@Component({
  selector: 'app-header-front',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './header-front.component.html',
  styleUrl: './header-front.component.scss'
})
export class HeaderFrontComponent implements OnInit {
  isLoggedIn: boolean = false;
  username: string | null = null;
  role: 'admin' | 'association' | 'donator' | null = null;
  @HostListener("window:scroll", [])
  onWindowScroll() {
    const header = document.querySelector(".header") as HTMLElement;
    if (window.scrollY > 50) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  }
  constructor(private router: Router, private authService: AuthService) {}
  ngOnInit(): void {
    this.isLoggedIn = !!this.authService.getToken();
    if (this.isLoggedIn) {
      this.username = localStorage.getItem('username');  // 👈 Doit être défini
      this.role = (this.authService.getRole?.() || localStorage.getItem('role')) as any;    }
  }
  
   get returnRoute(): string {
    if (!this.isLoggedIn) return '/login';
    switch (this.role) {
      case 'admin':        return '/dashboard';
      case 'association':  return '/dashboard-association';
      case 'donator':      return '/dashboard-donator';
      default:             return '/client';
    }
  }
  goToLogin() {
    this.router.navigate(['/login']);
  }

  goToRegister() {
    this.router.navigate(['/register']);
  }

  logout() {
    this.authService.logout();
    window.location.reload(); // Recharger la page pour rafraîchir l'affichage
  }
}



