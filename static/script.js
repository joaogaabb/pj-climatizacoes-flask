// ==========================================================================
// PJ Climatizações — interações do site
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Ano no rodapé ---------- */
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- Header: sombra/blur ao rolar ---------- */
  const header = document.getElementById('header');
  const onScrollHeader = () => {
    header.classList.toggle('is-scrolled', window.scrollY > 12);
  };
  onScrollHeader();
  window.addEventListener('scroll', onScrollHeader, { passive: true });

  /* ---------- Menu mobile ---------- */
  const menuToggle = document.getElementById('menuToggle');
  const nav = document.getElementById('nav');

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('is-open');
      menuToggle.classList.toggle('is-open', isOpen);
      menuToggle.setAttribute('aria-expanded', String(isOpen));
    });

    nav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        nav.classList.remove('is-open');
        menuToggle.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ---------- Accordion (FAQ) ---------- */
  const accordionItems = document.querySelectorAll('.acc-item');

  accordionItems.forEach((item) => {
    const trigger = item.querySelector('.acc-trigger');
    trigger.addEventListener('click', () => {
      const willOpen = !item.classList.contains('is-open');

      accordionItems.forEach((other) => {
        other.classList.remove('is-open');
        other.querySelector('.acc-trigger').setAttribute('aria-expanded', 'false');
      });

      if (willOpen) {
        item.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });
  });

  /* ---------- Carrossel de depoimentos ---------- */
  const track = document.getElementById('tTrack');
  const dotsWrap = document.getElementById('tDots');
  const prevBtn = document.getElementById('tPrev');
  const nextBtn = document.getElementById('tNext');

  if (track && dotsWrap) {
    const slides = Array.from(track.querySelectorAll('.t-slide'));
    let current = slides.findIndex((s) => s.classList.contains('is-active'));
    if (current < 0) current = 0;
    let autoTimer;

    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.className = 't-dot' + (i === current ? ' is-active' : '');
      dot.setAttribute('aria-label', `Ir para depoimento ${i + 1}`);
      dot.addEventListener('click', () => goTo(i));
      dotsWrap.appendChild(dot);
    });
    const dots = Array.from(dotsWrap.children);

    function goTo(index) {
      slides[current].classList.remove('is-active');
      dots[current].classList.remove('is-active');
      current = (index + slides.length) % slides.length;
      slides[current].classList.add('is-active');
      dots[current].classList.add('is-active');
      restartAuto();
    }

    function restartAuto() {
      clearInterval(autoTimer);
      autoTimer = setInterval(() => goTo(current + 1), 6000);
    }

    prevBtn.addEventListener('click', () => goTo(current - 1));
    nextBtn.addEventListener('click', () => goTo(current + 1));

    restartAuto();
  }

  /* ---------- Formulário de orçamento (envia para o Flask) ---------- */
  const form = document.getElementById('orcamentoForm');
  const feedback = document.getElementById('formFeedback');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!form.checkValidity()) {
        feedback.textContent = 'Preencha os campos obrigatórios antes de enviar.';
        feedback.style.color = '#CF5C29';
        form.reportValidity();
        return;
      }

      const botao = form.querySelector('button[type="submit"]');
      botao.disabled = true;
      feedback.textContent = 'Enviando...';
      feedback.style.color = '#12525A';

      try {
        // Manda os dados do formulário como JSON para a rota /orcamento do Flask
        const resposta = await fetch(form.action, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(Object.fromEntries(new FormData(form)))
        });
        const dados = await resposta.json();

        if (dados.ok) {
          feedback.textContent = dados.mensagem;
          feedback.style.color = '#12525A';
          form.reset();
        } else {
          feedback.textContent = dados.erros.join(' ');
          feedback.style.color = '#CF5C29';
        }
      } catch (erro) {
        feedback.textContent = 'Não foi possível enviar agora. Tente pelo WhatsApp.';
        feedback.style.color = '#CF5C29';
      } finally {
        botao.disabled = false;
      }
    });
  }

  /* ---------- Revelação suave ao rolar ---------- */
  const revealTargets = document.querySelectorAll('.section__head, .card, .feature, .step');

  if ('IntersectionObserver' in window && revealTargets.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    revealTargets.forEach((el) => observer.observe(el));
  } else {
    revealTargets.forEach((el) => el.classList.add('is-visible'));
  }

});
