import { Component, OnInit, AfterViewInit } from '@angular/core';
import * as Chartist from 'chartist';
import { CommonModule } from '@angular/common';
import { MatTooltipModule } from '@angular/material/tooltip'; 
import { AuthService } from 'app/services/auth.service';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);
@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  imports: [CommonModule, MatTooltipModule] // ✅ Import MatTooltipModule here
})
export class DashboardComponent implements OnInit, AfterViewInit {
stats: any;
assocTypeKeys: string[] = [];
assocPieChart: any;
assocTypeColors: {[key: string]: string} = {};
pieChart: any;

  constructor(private authService : AuthService) { }
    ngAfterViewInit() {
    // Pour s'assurer que le canvas est prêt
    if (this.stats) {
      this.initPieChart();
    }
  }
  startAnimationForLineChart(chart){
      let seq: any, delays: any, durations: any;
      seq = 0;
      delays = 80;
      durations = 500;

      chart.on('draw', function(data) {
        if(data.type === 'line' || data.type === 'area') {
          data.element.animate({
            d: {
              begin: 600,
              dur: 700,
              from: data.path.clone().scale(1, 0).translate(0, data.chartRect.height()).stringify(),
              to: data.path.clone().stringify(),
              easing: Chartist.Svg.Easing.easeOutQuint
            }
          });
        } else if(data.type === 'point') {
              seq++;
              data.element.animate({
                opacity: {
                  begin: seq * delays,
                  dur: durations,
                  from: 0,
                  to: 1,
                  easing: 'ease'
                }
              });
          }
      });

      seq = 0;
  };
  startAnimationForBarChart(chart){
      let seq2: any, delays2: any, durations2: any;

      seq2 = 0;
      delays2 = 80;
      durations2 = 500;
      chart.on('draw', function(data) {
        if(data.type === 'bar'){
            seq2++;
            data.element.animate({
              opacity: {
                begin: seq2 * delays2,
                dur: durations2,
                from: 0,
                to: 1,
                easing: 'ease'
              }
            });
        }
      });

      seq2 = 0;
  };
   ngOnInit() {
    this.authService.getAdminStats().subscribe({
      next: (data) => {
        this.stats = data;
        console.log("Stats:", this.stats);
        if (this.stats && this.stats.association_par_type) {
        this.assocTypeKeys = Object.keys(this.stats.association_par_type);
      }
        this.initPieChart();
      },
      error: (err) => {
        console.error(err);
      }
    });
  }

initPieChart() {
    // ✅ Line Chart : Montant par mois
    const montantData = {
      labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'],
      series: [this.stats.montant_par_mois]
    };
    new Chartist.Line('#montantParMoisChart', montantData, {
      low: 0,
      showArea: true
    });

    // ✅ Pie Chart sans donut + background gris + % en noir gras
    const rawLabels = Object.keys(this.stats.association_par_type);
    const rawValues = Object.values(this.stats.association_par_type) as number[];

    const labels: string[] = [];
    const data: number[] = [];
    let total = 0;
    rawLabels.forEach((label, idx) => {
      if (rawValues[idx] > 0) {
        labels.push(label);
        data.push(rawValues[idx]);
        total += rawValues[idx];
      }
    });
    // Détruit l'ancien si existe
    if (this.pieChart) {
      this.pieChart.destroy();
    }
   

    const colors = ['#f44336', '#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#00bcd4'];

     const ctx = document.getElementById('assocTypeChart') as HTMLCanvasElement;
    this.pieChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels.map((l, i) => `${l}: ${(data[i] / total * 100).toFixed(1)}%`),
        datasets: [{
          data: data,
          backgroundColor: ['#f44336', '#2196f3', '#4caf50', '#ff9800', '#9c27b0'],
          borderWidth: 1
        }]
      },
      options: {
        plugins: {
          legend: {
            position: 'right'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.parsed;
                const percent = (val / total * 100).toFixed(1);
                return `${context.label}: ${val} (${percent}%)`;
              }
            }
          }
        }
      }
    });
  }


}
