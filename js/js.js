/* =====================================
   REVEALS ARRIBA Y ABAJO
===================================== */

const reveals = document.querySelectorAll(".reveal-left, .reveal-right, .reveal-up");

if (reveals.length > 0) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("reveal-visible");
      } else {
        entry.target.classList.remove("reveal-visible");
      }
    });
  }, { threshold: 0.2 });

  reveals.forEach(el => revealObserver.observe(el));
}


/* =====================================
   BARRAS ANIMADAS
===================================== */

const bars = document.querySelectorAll(".progress");

if (bars.length > 0) {
  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const width = entry.target.dataset.width;
        entry.target.style.width = width + "%";
      } else {
        entry.target.style.width = "0%";
      }
    });
  }, { threshold: 0.35 });

  bars.forEach(bar => barObserver.observe(bar));
}


/* =====================================
   CONTADORES
===================================== */

const counters = document.querySelectorAll(".counter");

if (counters.length > 0) {
  const animatedCounters = new WeakSet();

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const counter = entry.target;
      const target = Number(counter.dataset.target);

      if (entry.isIntersecting && !animatedCounters.has(counter)) {
        animatedCounters.add(counter);

        let count = 0;

        const update = () => {
          count += target / 90;

          if (count < target) {
            counter.innerText = Math.ceil(count);
            requestAnimationFrame(update);
          } else {
            counter.innerText = target;
          }
        };

        update();
      }

      if (!entry.isIntersecting) {
        counter.innerText = "0";
        animatedCounters.delete(counter);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(counter => counterObserver.observe(counter));
}


/* =====================================
   CÍRCULOS ANIMADOS
===================================== */

const circleProgressItems = document.querySelectorAll(".circle-progress");

if (circleProgressItems.length > 0) {
  circleProgressItems.forEach(circle => {
    const fill = circle.querySelector(".circle-fill");

    if (!fill) return;

    const radius = fill.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;

    fill.style.strokeDasharray = `${circumference}`;
    fill.style.strokeDashoffset = `${circumference}`;
  });

  const circleObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const circle = entry.target;
      const fill = circle.querySelector(".circle-fill");

      if (!fill) return;

      const percent = Number(circle.dataset.percent);
      const radius = fill.r.baseVal.value;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (percent / 100) * circumference;

      if (entry.isIntersecting) {
        fill.style.strokeDashoffset = offset;
      } else {
        fill.style.strokeDashoffset = circumference;
      }
    });
  }, { threshold: 0.45 });

  circleProgressItems.forEach(circle => circleObserver.observe(circle));
}


/* =====================================
   HERO SLIDER HOME
===================================== */

const slidesBg = document.querySelectorAll(".hero-bg");
const slidesContent = document.querySelectorAll(".hero-content");
const dots = document.querySelectorAll(".dot");
const prevBtn = document.querySelector(".prev");
const nextBtn = document.querySelector(".next");

if (
  slidesBg.length > 0 &&
  slidesContent.length > 0 &&
  dots.length > 0 &&
  prevBtn &&
  nextBtn
) {
  let currentSlide = 0;
  let autoSlide;

  function showSlide(index) {
    slidesBg.forEach(slide => slide.classList.remove("active"));
    slidesContent.forEach(content => content.classList.remove("active"));
    dots.forEach(dot => dot.classList.remove("active"));

    slidesBg[index].classList.add("active");
    slidesContent[index].classList.add("active");
    dots[index].classList.add("active");

    currentSlide = index;
  }

  function nextSlide() {
    let next = currentSlide + 1;
    if (next >= slidesBg.length) {
      next = 0;
    }
    showSlide(next);
  }

  function prevSlide() {
    let prev = currentSlide - 1;
    if (prev < 0) {
      prev = slidesBg.length - 1;
    }
    showSlide(prev);
  }

  function startAutoSlide() {
    autoSlide = setInterval(() => {
      nextSlide();
    }, 6000);
  }

  function resetAutoSlide() {
    clearInterval(autoSlide);
    startAutoSlide();
  }

  nextBtn.addEventListener("click", () => {
    nextSlide();
    resetAutoSlide();
  });

  prevBtn.addEventListener("click", () => {
    prevSlide();
    resetAutoSlide();
  });

  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      const slideIndex = Number(dot.dataset.slide);
      showSlide(slideIndex);
      resetAutoSlide();
    });
  });

  showSlide(0);
  startAutoSlide();
}


/* =====================================
   SUBBARRA DE SERVICIOS
===================================== */

const serviceTabs = document.querySelectorAll(".service-tab");
const servicePanels = document.querySelectorAll(".service-panel");

if (serviceTabs.length > 0 && servicePanels.length > 0) {
  function activateServiceTab(targetId) {
    serviceTabs.forEach(tab => {
      if (tab.dataset.target === targetId) {
        tab.classList.add("active");
      } else {
        tab.classList.remove("active");
      }
    });
  }

  serviceTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.dataset.target;
      const targetPanel = document.getElementById(targetId);

      if (targetPanel) {
        const yOffset = -150;
        const y = targetPanel.getBoundingClientRect().top + window.pageYOffset + yOffset;

        window.scrollTo({
          top: y,
          behavior: "smooth"
        });

        activateServiceTab(targetId);
      }
    });
  });

  const panelObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        activateServiceTab(entry.target.id);
      }
    });
  }, { threshold: 0.5 });

  servicePanels.forEach(panel => panelObserver.observe(panel));
}


/* =====================================
   TESTIMONIOS EMPLEO
===================================== */

const testimonialSlides = document.querySelectorAll(".jobs-testimonial-slide");
const testimonialDots = document.querySelectorAll(".jobs-dot");

if (testimonialSlides.length > 0 && testimonialDots.length > 0) {
  testimonialDots.forEach(dot => {
    dot.addEventListener("click", () => {
      const index = Number(dot.dataset.slide);

      testimonialSlides.forEach(slide => slide.classList.remove("active"));
      testimonialDots.forEach(btn => btn.classList.remove("active"));

      if (testimonialSlides[index]) {
        testimonialSlides[index].classList.add("active");
      }

      dot.classList.add("active");
    });
  });
}