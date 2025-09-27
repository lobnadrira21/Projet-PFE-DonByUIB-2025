import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';
import { AjoutDonComponent } from 'app/components/ajout-don/ajout-don.component';
import { AuthService } from 'app/services/auth.service';

@Component({
  selector: 'app-gestion-dons',
  standalone: true,
  imports: [MatButtonModule, MatTooltipModule,RouterModule, CommonModule,
       FormsModule, 
          MatFormFieldModule,  
          MatInputModule,  
          MatDialogModule, 
            
          MatIconModule,
          ReactiveFormsModule],
  templateUrl: './gestion-dons.component.html',
  styleUrl: './gestion-dons.component.scss'
})
export class GestionDonsComponent implements OnInit {
dons: any[] = [];

  trackById = (_: number, d: any) => d.id_don ?? d.id;

  constructor(
    private authService: AuthService,
    private http: HttpClient,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.getDons();
  }

  getDons(): void {
  
    this.authService.getAllDonsAdmin().subscribe({
      next: (data) => this.dons = data,
      error: (err) => console.error('❌ Erreur lors du chargement des dons', err)
    });

  
  }

  openAddDonModal(): void {
    const dialogRef = this.dialog.open(AjoutDonComponent, {
      width: '700px',
      disableClose: true
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.getDons(); 
      }
    });
  }

  deleteDon(id: number) {
    if (!confirm("Êtes-vous sûr de vouloir supprimer ce don ?")) return;

    this.authService.deleteDon(id).subscribe({
      next: () => {
     
        this.dons = this.dons.filter(d => (d.id_don ?? d.id) !== id);

       
      },
      error: (err) => console.error("Erreur de suppression :", err)
    });
  }

}

