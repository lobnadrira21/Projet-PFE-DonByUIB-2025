import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink, RouterModule } from '@angular/router';
import { HeaderFrontComponent } from '../header-front/header-front.component';

@Component({
  selector: 'app-fail',

  templateUrl: './fail.component.html',
  styleUrl: './fail.component.scss',
  standalone: true,
  imports: [CommonModule, HeaderFrontComponent, RouterModule],
})
export class FailComponent {

}
