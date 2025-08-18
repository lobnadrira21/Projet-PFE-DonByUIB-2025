import { Component } from '@angular/core';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { TypeAssociation } from 'app/models/type-association.model';




@Component({
  selector: 'app-ajout-association',
  standalone: true,
  imports: [RouterModule, 
    CommonModule,
    FormsModule,  // ✅ Required for [(ngModel)]
    MatFormFieldModule,  // ✅ Required for <mat-form-field>
    MatInputModule,  // ✅ Required for matInput
    MatDialogModule,  // ✅ Required for the modal/dialog
    MatButtonModule,  // ✅ Required for buttons
    MatIconModule,
    MatSelectModule  // ✅ Required for Material icons
  ],
  templateUrl: './ajout-association.component.html',
  styleUrl: './ajout-association.component.scss'
})


export class AjoutAssociationComponent {
   typesAssociation: string[] = Object.values(TypeAssociation);
   gouvernorats: any[] = [];
  association = {
    nom_complet: '',
    email: '',
    telephone: '',
    description_association: '',
    adresse: '',
    type_association: '',
    password: '',
    gouvernorat_id: ''
    
  };

  constructor(
    public dialogRef: MatDialogRef<AjoutAssociationComponent>,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
  this.loadGouvernorats();
}

  loadGouvernorats(): void {
  const token = localStorage.getItem('token');
  this.http.get<any[]>('http://localhost:5000/gouvernorats', {
    headers: { Authorization: `Bearer ${token}` }
  }).subscribe({
    next: (data) => this.gouvernorats = data,
    error: (err) => console.error('Erreur chargement gouvernorats', err)
  });
}

  onNoClick(): void {
    this.dialogRef.close();
  }

  isValid(): boolean {
  return (
    this.association.nom_complet.trim() !== '' &&
    this.association.email.trim() !== '' &&
    this.association.telephone.trim() !== '' &&
    this.association.adresse.trim() !== '' &&
    this.association.type_association.trim() !== '' &&
    this.association.password.trim() !== '' &&
    !!this.association.gouvernorat_id  
  );
}


  addAssociation(): void {
    if (this.isValid()) {
      const token = localStorage.getItem('token'); // ✅ Retrieve JWT token from local storage
  
      this.http.post('http://localhost:5000/create-association', this.association, {
        headers: { Authorization: `Bearer ${token}` } // ✅ Attach token
      }).subscribe({
        next: (response) => {
          console.log('Success:', response);
          this.dialogRef.close(response);
        },
        error: (error) => {
          console.error('Error:', error);
          if (error.status === 401) {
            alert('Vous devez être connecté pour ajouter une association.');
          } else {
            alert('Erreur lors de la création de l\'association.');
          }
        }
      });
    }
  }
  
}