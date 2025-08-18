import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { Router } from '@angular/router';
import { AuthService } from 'app/services/auth.service';

@Component({
  selector: 'app-modifierprofil',
  standalone: true,
  imports: [ MatFormFieldModule,  // ✅ Import Material Form Field
      MatInputModule,      // ✅ Import Material Input
      MatButtonModule,
      ReactiveFormsModule,],
  templateUrl: './modifierprofil.component.html',
  styleUrl: './modifierprofil.component.scss'
})
export class ModifierprofilComponent implements OnInit {
 profileForm!: FormGroup;
  message = '';
  extractedData: any = null;


  constructor(private fb: FormBuilder, private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    this.profileForm = this.fb.group({
      nom_complet: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      telephone: ['', Validators.required],
      old_password: [''],
      new_password: ['']
    });

    // Optionnel : pré-remplir les champs
    this.authService.getProfileDonator().subscribe((res: any) => {
      this.profileForm.patchValue({
        nom_complet: res.nom_complet,
        email: res.email,
        telephone: res.telephone
      });
    });
  }

 

  updateProfileDonator() {
    if (this.profileForm.invalid) return;

    const formData = new FormData();
    Object.keys(this.profileForm.controls).forEach(key => {
      formData.append(key, this.profileForm.get(key)?.value);
    });

   

    this.authService.modifyProfileDonator(formData).subscribe({
      next: (res: any) => {
        this.message = res.message;
        this.extractedData = res.extracted_data;
      },
      error: (err) => {
        this.message = err.error?.error || 'Erreur lors de la mise à jour';
      }
    });
  }

}
