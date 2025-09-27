import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GestionDonsComponent } from './gestion-dons.component';

describe('GestionDonsComponent', () => {
  let component: GestionDonsComponent;
  let fixture: ComponentFixture<GestionDonsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GestionDonsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(GestionDonsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
