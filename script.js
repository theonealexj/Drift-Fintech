/* ================================================================
   DRIFT – JavaScript: Particles, Animations, Calculator, UX
   ================================================================ */

'use strict';

// ──── Particle System ────
(function initParticles() {
  const canvas = document.getElementById('particleCanvas');
  const ctx = canvas.getContext('2d');
  let particles = [];
  let W, H;
  let animId;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function randomBetween(a, b) { return a + Math.random() * (b - a); }

  function createParticle() {
    return {
      x: randomBetween(0, W),
      y: randomBetween(0, H),
      r: randomBetween(0.4, 2.2),
      baseX: 0,
      baseY: 0,
      vx: randomBetween(-0.15, 0.15),
      vy: randomBetween(-0.25, -0.05),
      alpha: randomBetween(0.1, 0.7),
      color: Math.random() > 0.5
        ? `rgba(0, 255, 136, `
        : Math.random() > 0.5
          ? `rgba(77, 166, 255, `
          : `rgba(168, 85, 247, `
    };
  }

  const PARTICLE_COUNT = 120;
  for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(createParticle());

  function drawParticle(p) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = p.color + p.alpha + ')';
    ctx.fill();
  }

  // Occasional connecting lines between nearby particles
  function connectNearby() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 100) {
          const alpha = (1 - dist / 100) * 0.12;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 255, 136, ${alpha})`;
          ctx.lineWidth = 0.4;
          ctx.stroke();
        }
      }
    }
  }

  function tick() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.y < -10) {
        p.y = H + 10;
        p.x = randomBetween(0, W);
      }
      if (p.x < -10) p.x = W + 10;
      if (p.x > W + 10) p.x = -10;
      drawParticle(p);
    });
    connectNearby();
    animId = requestAnimationFrame(tick);
  }
  tick();
})();


// ──── Navbar Scroll Effect ────
(function initNavbar() {
  const nav = document.getElementById('navbar');
  function onScroll() {
    if (window.scrollY > 40) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
})();

// ──── Hamburger Menu ────
(function initHamburger() {
  const btn = document.getElementById('hamburger');
  const links = document.querySelector('.nav-links');
  if (!btn || !links) return;
  btn.addEventListener('click', () => {
    const isOpen = links.style.display === 'flex';
    links.style.display = isOpen ? 'none' : 'flex';
    links.style.flexDirection = 'column';
    links.style.position = 'absolute';
    links.style.top = '72px';
    links.style.left = '0';
    links.style.right = '0';
    links.style.background = 'rgba(5,5,20,0.97)';
    links.style.padding = '20px 24px';
    links.style.gap = '18px';
    links.style.backdropFilter = 'blur(20px)';
    links.style.borderBottom = '1px solid rgba(255,255,255,0.06)';
  });
})();


// ──── Scroll Reveal ────
(function initReveal() {
  const els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;
  const io = new IntersectionObserver(
    (entries) => entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('revealed');
        io.unobserve(e.target);
      }
    }),
    { threshold: 0.15 }
  );
  els.forEach(el => io.observe(el));
})();


// ──── Risk Meter Animation ────
(function initRiskMeter() {
  const fill = document.getElementById('riskFill');
  const thumb = document.getElementById('riskThumb');
  if (!fill || !thumb) return;

  const io = new IntersectionObserver(
    (entries) => entries.forEach(e => {
      if (e.isIntersecting) {
        setTimeout(() => {
          fill.style.width = '20%';
          thumb.style.left = '20%';
        }, 400);
        io.unobserve(e.target);
      }
    }),
    { threshold: 0.3 }
  );
  io.observe(fill.parentElement);
})();


// ──── Calculator Logic ────
(function initCalculator() {
  const dailyInput = document.getElementById('dailyAmount');
  const returnInput = document.getElementById('returnRate');
  const dailyDisp = document.getElementById('dailyDisplay');
  const returnDisp = document.getElementById('returnDisplay');
  const y1El = document.getElementById('year1');
  const y3El = document.getElementById('year3');
  const y5El = document.getElementById('year5');
  const bar1 = document.getElementById('bar1');
  const bar2 = document.getElementById('bar2');
  const bar3 = document.getElementById('bar3');
  if (!dailyInput) return;

  function fmtINR(val) {
    if (val >= 10000000) return '₹' + (val / 10000000).toFixed(1) + 'Cr';
    if (val >= 100000) return '₹' + (val / 100000).toFixed(1) + 'L';
    if (val >= 1000) return '₹' + (val / 1000).toFixed(1) + 'K';
    return '₹' + Math.round(val).toLocaleString('en-IN');
  }

  // Compound future value of a daily annuity
  function calcFV(daily, ratePct, years) {
    const n = years * 365;
    const r = ratePct / 100 / 365;
    if (r === 0) return daily * n;
    return daily * ((Math.pow(1 + r, n) - 1) / r);
  }

  function updateBars(v1, v3, v5) {
    const max = v5;
    bar1.style.height = Math.max(5, (v1 / max) * 100) + '%';
    bar2.style.height = Math.max(5, (v3 / max) * 100) + '%';
    bar3.style.height = '95%';
  }

  function updateCalc() {
    const daily = parseFloat(dailyInput.value);
    const rate = parseFloat(returnInput.value);
    dailyDisp.textContent = daily;
    returnDisp.textContent = rate;

    const v1 = calcFV(daily, rate, 1);
    const v3 = calcFV(daily, rate, 3);
    const v5 = calcFV(daily, rate, 5);

    y1El.textContent = fmtINR(v1);
    y3El.textContent = fmtINR(v3);
    y5El.textContent = fmtINR(v5);

    updateBars(v1, v3, v5);
  }

  dailyInput.addEventListener('input', updateCalc);
  returnInput.addEventListener('input', updateCalc);
  updateCalc(); // initial

  // Animate bars on scroll into view
  const barChart = document.querySelector('.bar-chart');
  if (barChart) {
    const io = new IntersectionObserver(
      entries => entries.forEach(e => {
        if (e.isIntersecting) {
          updateCalc();
          io.unobserve(e.target);
        }
      }),
      { threshold: 0.4 }
    );
    io.observe(barChart);
  }
})();


// ──── Parallax on Hero ────
(function initParallax() {
  const hero = document.getElementById('hero');
  const orbit = document.getElementById('coinOrbit');
  if (!hero || !orbit) return;

  window.addEventListener('scroll', () => {
    const sy = window.scrollY;
    if (sy < window.innerHeight) {
      orbit.style.transform = `translateY(calc(-55% + ${sy * 0.15}px))`;
    }
  }, { passive: true });
})();


// ──── Orbit Coins: auto-counter-rotate so they stay upright ────
// Handled by CSS animations with counter-rotation on the coin itself.


// ──── Crash Alerts: replay animation on scroll into view ────
(function initAlerts() {
  const alertsSection = document.querySelector('.alerts-wrap');
  if (!alertsSection) return;
  const popups = alertsSection.querySelectorAll('.alert-popup, .tooltip-popup');

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        popups.forEach(p => {
          p.style.animation = 'none';
          void p.offsetHeight; // reflow
          p.style.animation = '';
        });
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });
  io.observe(alertsSection);
})();


// ──── Waitlist Form ────
window.submitWaitlist = function (e) {
  e.preventDefault();
  const name = document.getElementById('nameInput').value.trim();
  const email = document.getElementById('emailInput').value.trim();
  if (!name || !email) {
    // Simple shake on empty
    const form = document.getElementById('waitlistForm');
    form.style.animation = 'none';
    void form.offsetHeight;
    form.style.animation = 'shake 0.4s ease';
    return;
  }
  const emailRx = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRx.test(email)) {
    alert('Please enter a valid email address.');
    return;
  }
  document.getElementById('waitlistForm').style.display = 'none';
  document.getElementById('successMsg').style.display = 'block';
  document.getElementById('successMsg').style.animation = 'fadeSlideIn 0.6s ease';

  // Custom: Redirect to dashboard after 2 seconds to simulate entry
  setTimeout(() => {
    window.location.href = 'dashboard.html';
  }, 2000);
};

window.shareOnWhatsApp = function () {
  const text = encodeURIComponent('🚀 I just joined Drift — the micro-investing crypto app for college students! Invest ₹10 at a time. Join me: https://driftinvest.in');
  window.open(`https://wa.me/?text=${text}`, '_blank');
};

window.shareOnTwitter = function () {
  const text = encodeURIComponent('Just joined @DriftInvest — a micro-crypto investing app for students! ₹10/day could change your future 🌙 #Crypto #FinTech #GenZ');
  window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
};


// ──── Smooth Active Nav Link Highlighting ────
(function initActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');
  if (!sections.length) return;

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        navLinks.forEach(l => {
          l.style.color = l.getAttribute('href') === `#${e.target.id}`
            ? 'var(--text-primary)' : '';
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => io.observe(s));
})();


// ──── CSS Shake Animation (injected) ────
(function injectShake() {
  const s = document.createElement('style');
  s.textContent = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      20%       { transform: translateX(-8px); }
      40%       { transform: translateX(8px); }
      60%       { transform: translateX(-5px); }
      80%       { transform: translateX(5px); }
    }
  `;
  document.head.appendChild(s);
})();


// ──── Coin Hover Effect ────
(function initCoinHover() {
  const coins = document.querySelectorAll('.crypto-coin');
  coins.forEach(c => {
    c.addEventListener('mouseenter', () => {
      c.style.transform = 'scale(1.2)';
      c.style.transition = 'transform 0.3s ease';
    });
    c.addEventListener('mouseleave', () => {
      c.style.transform = 'scale(1)';
    });
  });
})();


// ──── Glowing cursor trail (subtle) ────
(function initCursorTrail() {
  const dots = [];
  const NUM = 8;
  for (let i = 0; i < NUM; i++) {
    const d = document.createElement('div');
    d.style.cssText = `
      position: fixed; pointer-events: none; z-index: 9999;
      width: ${6 - i * 0.5}px; height: ${6 - i * 0.5}px;
      border-radius: 50%;
      background: rgba(0, 255, 136, ${0.35 - i * 0.03});
      box-shadow: 0 0 ${8 - i}px rgba(0,255,136,0.4);
      transition: transform 0.05s;
      left: -10px; top: -10px;
    `;
    document.body.appendChild(d);
    dots.push(d);
  }
  let mx = -100, my = -100;
  let positions = Array(NUM).fill({ x: -100, y: -100 });

  window.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });

  function trail() {
    positions[0] = { x: mx, y: my };
    for (let i = 1; i < NUM; i++) {
      positions[i] = {
        x: positions[i - 1].x * 0.4 + (positions[i] || positions[i - 1]).x * 0.6,
        y: positions[i - 1].y * 0.4 + (positions[i] || positions[i - 1]).y * 0.6
      };
    }
    dots.forEach((d, i) => {
      d.style.left = (positions[i].x - 3) + 'px';
      d.style.top = (positions[i].y - 3) + 'px';
    });
    requestAnimationFrame(trail);
  }
  trail();
})();


// ──── Learn card expand (micro interaction) ────
(function initLearnCards() {
  const cards = document.querySelectorAll('.learn-card');
  cards.forEach(card => {
    card.addEventListener('click', () => {
      const prev = document.querySelector('.learn-card.expanded');
      if (prev && prev !== card) prev.classList.remove('expanded');
      card.classList.toggle('expanded');
    });
  });

  const s = document.createElement('style');
  s.textContent = `
    .learn-card.expanded {
      border-color: rgba(77, 166, 255, 0.4) !important;
      box-shadow: 0 12px 50px rgba(77, 166, 255, 0.15) !important;
      transform: translateY(-6px) !important;
    }
  `;
  document.head.appendChild(s);
})();


// ──── Micro-animation: number count-up for trust bar ────
(function initCountUp() {
  function countUp(el, target, duration, prefix, suffix) {
    const start = performance.now();
    const isFloat = !Number.isInteger(target);
    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const val = target * ease;
      el.textContent = prefix + (isFloat ? val.toFixed(1) : Math.round(val).toLocaleString('en-IN')) + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const trustBar = document.querySelector('.trust-bar');
  if (!trustBar) return;

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const vals = trustBar.querySelectorAll('.trust-val');
        if (vals[0]) countUp(vals[0], 12000, 1400, '', '+');
        if (vals[1]) {
          let t = 0;
          const dur = 1400;
          const start = performance.now();
          function tick(now) {
            const frac = Math.min((now - start) / dur, 1);
            const ease = 1 - Math.pow(1 - frac, 3);
            vals[1].textContent = '₹' + (2.4 * ease).toFixed(1) + 'Cr';
            if (frac < 1) requestAnimationFrame(tick);
          }
          requestAnimationFrame(tick);
        }
        if (vals[2]) {
          vals[2].style.transition = 'none';
          let t = 0;
          const dur = 1200;
          const st = performance.now();
          function tck(now) {
            const f = Math.min((now - st) / dur, 1);
            const ease = 1 - Math.pow(1 - f, 3);
            vals[2].textContent = (99 + 0.9 * ease).toFixed(1) + '%';
            if (f < 1) requestAnimationFrame(tck);
          }
          requestAnimationFrame(tck);
        }
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  io.observe(trustBar);
})();
