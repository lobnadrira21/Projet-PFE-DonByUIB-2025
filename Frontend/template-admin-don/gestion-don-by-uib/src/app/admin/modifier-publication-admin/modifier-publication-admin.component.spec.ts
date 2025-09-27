import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModifierPublicationAdminComponent } from './modifier-publication-admin.component';

describe('ModifierPublicationAdminComponent', () => {
  let component: ModifierPublicationAdminComponent;
  let fixture: ComponentFixture<ModifierPublicationAdminComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModifierPublicationAdminComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ModifierPublicationAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
