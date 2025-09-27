import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatIcon } from '@angular/material/icon';
import { Router, RouterModule } from '@angular/router';
import { AjoutPublicationComponent } from 'app/components/ajout-publication/ajout-publication.component';
import { DetailPublicationComponent } from 'app/components/detail-publication/detail-publication.component';
import { AuthService } from 'app/services/auth.service';

@Component({
  selector: 'app-gestion-publication',
  standalone: true,
  imports: [MatIcon, CommonModule,RouterModule],
  templateUrl: './gestion-publication.component.html',
  styleUrl: './gestion-publication.component.scss'
})
export class GestionPublicationComponent {
  
    publications: any[] = [];
    
  
    constructor(
      private authService: AuthService,
   
      private http: HttpClient,
      private dialog: MatDialog,
      private router: Router
    ) {
    
    }
  
    ngOnInit(): void {
      this.getMyPublications();
    }
    openAddPubModal(): void {
      const dialogRef = this.dialog.open(AjoutPublicationComponent, {
        width: '700px',
        disableClose: true
      });
  
      dialogRef.afterClosed().subscribe(result => {
      if (result) {
      
        this.getMyPublications();
      }
    });
  }
  
   deletePublication(id: number) {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette publication ?")) return;

    this.authService.deletePublication(id).subscribe({
      next: () => {
  
        this.publications = this.publications.filter(p => (p.id_publication ?? p.id) !== id);
     
      },
      error: err => console.error("Erreur de suppression :", err)
    });
  }


  
    
    
      getMyPublications(): void {
        this.authService.getPublications().subscribe({
          next: (data) => {
            this.publications = data;
          },
          error: (err) => {
            console.error("Erreur chargement publications :", err);
          }
        });
      }
    
    
     modifierPublication(id: number): void {
    this.router.navigate(['/dashboard/modifier-publication-admin', id]);
  }
 openDetailPublication(id: number): void {
    this.dialog.open(DetailPublicationComponent, {
      width: '600px',
      data: { id }
    });
  }
  
    
     
    
  }
  
  


