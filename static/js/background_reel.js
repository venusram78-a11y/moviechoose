const BackgroundReel = {
    slides: [],
    current: 0,
    interval: null,
    init() {
        this.slides = Array.from(document.querySelectorAll(".backdrop-slide"));
        if (!this.slides.length) return;
        this.slides.forEach((slide) => {
            const src = slide.dataset.src;
            if (src) {
                const img = new Image();
                img.onload = () => (slide.style.backgroundImage = `url(${src})`);
                img.src = src;
            }
        });
        setTimeout(() => this.activate(0), 500);
        const start = () => {
            this.interval = setInterval(() => {
                this.current = (this.current + 1) % this.slides.length;
                this.activate(this.current);
            }, 5000);
        };
        start();
        document.addEventListener("visibilitychange", () => {
            clearInterval(this.interval);
            if (!document.hidden) start();
        });
    },
    activate(index) {
        this.slides.forEach((s, i) => s.classList.toggle("active", i === index));
    },
};
document.addEventListener("DOMContentLoaded", () => BackgroundReel.init());
