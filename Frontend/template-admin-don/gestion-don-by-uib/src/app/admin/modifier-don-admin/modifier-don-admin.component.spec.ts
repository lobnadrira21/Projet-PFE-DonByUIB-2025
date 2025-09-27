import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModifierDonAdminComponent } from './modifier-don-admin.component';

describe('ModifierDonAdminComponent', () => {
  let component: ModifierDonAdminComponent;
  let fixture: ComponentFixture<ModifierDonAdminComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModifierDonAdminComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ModifierDonAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
