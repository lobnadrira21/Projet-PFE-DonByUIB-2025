import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, NgZone } from '@angular/core';
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
 sentimentsDonutChart?: Chart;
  sentimentsMonthlyChart?: Chart;

 pubSentimentsChart?: Chart;

@ViewChild('pubSentimentsCanvas') pubCanvas?: ElementRef<HTMLCanvasElement>;
  constructor(private authService : AuthService, private zone: NgZone) { }
    ngAfterViewInit() {
    // Pour s'assurer que le canvas est prêt
    
      if (this.stats) {
          this.initPieChart();
       this.initSentimentCharts();
      this.zone.runOutsideAngular(() => {
        setTimeout(() => this.initPubSentimentsChart(), 0);
      });
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

       this.zone.runOutsideAngular(() => {
          setTimeout(() => this.initPubSentimentsChart(), 0);
            this.initPieChart();
        this.initSentimentCharts();
        
        });
      },
      error: (err) => console.error(err)
    });
      
     
  }
   private initPubSentimentsChart() {
    const list = this.stats?.sentiments_par_publication as Array<any> | undefined;
    if (!list || !list.length) return;

    const el = this.pubCanvas?.nativeElement;
    if (!el) return;

    const labels = list.map(x => x.titre);
    const dataPos = list.map(x => x.positif || 0);
    const dataNeu = list.map(x => x.neutre  || 0);
    const dataNeg = list.map(x => (x.negatif ?? x['négatif'] ?? 0));

    // (re)destroy si besoin
    this.pubSentimentsChart?.destroy();

    this.pubSentimentsChart = new Chart(el, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Positif', data: dataPos, backgroundColor: '#4caf50' },
          { label: 'Neutre',  data: dataNeu, backgroundColor: '#9e9e9e' },
          { label: 'Négatif', data: dataNeg, backgroundColor: '#f44336' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false, // important quand la hauteur est gérée en CSS
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              title: (items) => labels[items[0].dataIndex]
            }
          }
        },
        scales: {
          x: {
            stacked: true,
            ticks: {
              maxRotation: 0,
              minRotation: 0,
              callback: (_: any, i: number) => {
                const t = labels[i] || '';
                return t.length > 18 ? t.slice(0, 18) + '…' : t;
              }
            }
          },
          y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } }
        }
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


   private initSentimentCharts() {
    if (!this.stats) return;

    // valeurs globales (attention à l’accent de "négatif")
    const pos = this.stats?.sentiments?.positif || 0;
    const neg = (this.stats?.sentiments?.['négatif'] ?? this.stats?.sentiments?.negatif) || 0;
    const neu = this.stats?.sentiments?.neutre || 0;

    // Doughnut global
    const donutEl = document.getElementById('sentimentsDonut') as HTMLCanvasElement | null;
    if (donutEl) {
      if (this.sentimentsDonutChart) this.sentimentsDonutChart.destroy();
      this.sentimentsDonutChart = new Chart(donutEl, {
        type: 'doughnut',
        data: {
          labels: ['Positif', 'Neutre', 'Négatif'],
          datasets: [{
            data: [pos, neu, neg],
            backgroundColor: ['#4caf50', '#9e9e9e', '#f44336']
          }]
        },
        options: {
          plugins: { legend: { position: 'bottom' } },
          cutout: '55%'
        }
      });
    }

    // Bar mensuel (si dispo)
    const labels = this.stats?.sentiments_par_mois?.labels || [];
    const mPos   = this.stats?.sentiments_par_mois?.positif || [];
    const mNeu   = this.stats?.sentiments_par_mois?.neutre  || [];
    const mNeg   = this.stats?.sentiments_par_mois?.negatif || []; // (backend renvoie "negatif" sans accent ici)

    const barEl = document.getElementById('sentimentsMonthlyBar') as HTMLCanvasElement | null;
    if (barEl && labels.length) {
      if (this.sentimentsMonthlyChart) this.sentimentsMonthlyChart.destroy();
      this.sentimentsMonthlyChart = new Chart(barEl, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            { label: 'Positif', data: mPos, backgroundColor: '#4caf50' },
            { label: 'Neutre',  data: mNeu, backgroundColor: '#9e9e9e' },
            { label: 'Négatif', data: mNeg, backgroundColor: '#f44336' }
          ]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom' } },
          scales: {
            y: { beginAtZero: true, ticks: { precision: 0 } }
          }
        }
      });
    }
  }


}
