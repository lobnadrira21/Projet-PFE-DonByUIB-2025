import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GestionPublicationComponent } from './gestion-publication.component';

describe('GestionPublicationComponent', () => {
  let component: GestionPublicationComponent;
  let fixture: ComponentFixture<GestionPublicationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GestionPublicationComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(GestionPublicationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
