import { Component, OnInit } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { FormBuilder, FormGroup, Validators ,ReactiveFormsModule, FormsModule} from '@angular/forms';
import { AuthService } from 'app/services/auth.service';
import { Router } from '@angular/router';
import { TypeAssociation } from 'app/models/type-association.model';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
@Component({
  selector: 'app-user-profile',
  standalone:true,
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.css'],
  imports: [
    MatFormFieldModule,  // ✅ Import Material Form Field
    MatInputModule,      // ✅ Import Material Input
    MatButtonModule,
    ReactiveFormsModule,
    MatSelectModule,
FormsModule,
MatIconModule,
MatCardModule,
MatDividerModule
  ]
})
export class UserProfileComponent implements OnInit {
typesAssociation: string[] = Object.values(TypeAssociation);


  profileForm!: FormGroup;
  message: string = '';
  gouvernorats: any[] = [];
selectedGouvernoratId: number | null = null;
gouvernorat_id: [''] //
showOld = false;
showNew = false;

  constructor(private authService: AuthService, private fb: FormBuilder,private router: Router) {}

  ngOnInit() {
    // Initialize form
    this.typesAssociation = Object.values(TypeAssociation);
    this.profileForm = this.fb.group({
  nom_complet: ['', Validators.required],
  email: ['', [Validators.required, Validators.email]],
  description_association: [''],
  telephone: ['', Validators.required],
  adresse: ['', Validators.required],
  type_association: ['', Validators.required],
  gouvernorat_id: [null],  // ✅ Ajouté ici
  old_password: [''],
  new_password: [''],
  photo: [''],
   matricule_fiscal: [''],   
  releve_rib: [''],        
  cin_fiscale: ['']  
});

    this.loadGouvernorats();
     this.loadProfile();
  }


  selectedCinFile: File | null = null;

onCinFiscaleSelected(event: any): void {
  const file = event.target.files[0];
  if (file) {
    this.selectedCinFile = file;
  }
}

 
  photoPreview: string | ArrayBuffer | null = null;
  selectedFile: File | null = null;
  
  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
  
      const reader = new FileReader();
      reader.onload = () => {
        this.photoPreview = reader.result;
      };
      reader.readAsDataURL(file);
    }
  }
  
  loadGouvernorats() {
  this.authService.getGouvernorats().subscribe({
    next: (data) => this.gouvernorats = data,
    error: (err) => console.error('Erreur chargement gouvernorats', err)
  });
}
  updateProfile() {
    if (this.profileForm.invalid) return;

    const formData = new FormData();
  
    // Ajouter les champs du formulaire dans FormData
    Object.keys(this.profileForm.controls).forEach(key => {
      const value = this.profileForm.get(key)?.value;
      formData.append(key, value);
    });
  
    // Ajouter la photo si elle est sélectionnée
    if (this.selectedFile) {
      formData.append('photo_file', this.selectedFile); // 🔁 nom attendu par Flask
    }
    // Ajouter la photo si sélectionnée
if (this.selectedFile) {
  formData.append('photo_file', this.selectedFile);
}

// Ajouter la CIN fiscale si sélectionnée
if (this.selectedCinFile) {
  formData.append('cin_fiscale_file', this.selectedCinFile);
}

  
    const token = this.authService.getToken();
    if (!token) {
      console.error("No token found. User is not authenticated.");
      return;
    }
    const gouvernoratId = this.profileForm.get('gouvernorat_id')?.value;
if (gouvernoratId) {
  formData.append('gouvernorat_id', gouvernoratId.toString());
}


  
    this.authService.modifyProfile(formData).subscribe(
      (response) => {
        console.log("Profile updated successfully:", response);
        this.message = "Profil mis à jour avec succès !";
        setTimeout(() => {
          this.router.navigate(['/dashboard-association/accueil-association']);
        }, 1000);
      },

      (error) => {
        console.error("Error updating profile:", error);
        this.message = error.error?.error || "Erreur lors de la mise à jour du profil.";
      }
    );
    
  }
  
  /** Handle form submission */
  loadProfile() {
  this.authService.getProfile().subscribe(
    (data) => {
      this.profileForm.patchValue(data);
      
    },
    (error) => {
      console.error("Error fetching profile:", error);
    }
  );
}
resetForm() {
  this.profileForm.reset(this.profileForm.getRawValue());
}
}