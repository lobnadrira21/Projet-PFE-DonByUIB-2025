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
 private initialValue!: any;

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
  nom_complet: [''],
  email: ['', [Validators.email]], 
  description_association: [''],
  telephone: [''],
  adresse: [''],
  type_association: [''],
  gouvernorat_id: [null],  
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
    if (this.profileForm.pristine) return; // rien à envoyer

    const formData = new FormData();

    // 🔁 Ajoute seulement les champs réellement modifiés et non vides
    Object.keys(this.profileForm.controls).forEach((key) => {
      const control = this.profileForm.get(key);
      if (!control) return;

      // champ modifié ?
      const changed = control.dirty && control.value !== this.initialValue?.[key];

      // on ignore les vides (''/null/undefined) pour éviter d’écraser côté backend
      const hasValue =
        control.value !== '' &&
        control.value !== null &&
        control.value !== undefined;

      if (changed && hasValue) {
        // gouvernorat_id: number → string
        const val = key === 'gouvernorat_id' ? String(control.value) : control.value;
        formData.append(key, val);
      }
    });

    // 📎 Fichiers (toujours si sélectionnés)
    if (this.selectedFile) formData.append('photo_file', this.selectedFile);
    if (this.selectedCinFile) formData.append('cin_fiscale_file', this.selectedCinFile);

    // 🗝️ Token (si besoin côté service)
    const token = this.authService.getToken();
    if (!token) return console.error("No token found.");

    this.authService.modifyProfile(formData).subscribe({
      next: (res) => {
        this.message = "Profil mis à jour avec succès !";
        // ✅ Après succès, on remet la base des valeurs
        this.initialValue = this.profileForm.getRawValue();
        this.profileForm.markAsPristine();
        setTimeout(() => this.router.navigate(['/dashboard-association/accueil-association']), 800);
      },
      error: (err) => {
        console.error("Error updating profile:", err);
        this.message = err.error?.error || "Erreur lors de la mise à jour du profil.";
      }
    });
  }
  
  /** Handle form submission */
  loadProfile() {
    this.authService.getProfile().subscribe(
      (data) => {
        this.profileForm.patchValue(data);
        // 🧷 Garde une copie pour détecter les changements
        this.initialValue = this.profileForm.getRawValue();
        this.profileForm.markAsPristine();
      },
      (error) => console.error("Error fetching profile:", error)
    );
  }
 resetForm() {
    this.profileForm.reset(this.initialValue); // ↩️ revenir aux valeurs chargées
    this.profileForm.markAsPristine();
  }
}