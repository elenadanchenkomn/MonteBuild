
import './App.css';

function App() {
  return (
    
    <div className="App">
    <header className="App-header">
      <div ><img className="logo" src="./img/logo2.png" alt="logo"></img></div>
      <ul className="navigation">
        <li className="nav-list">О нас</li>
        <li className="nav-list">Контакты</li>
        <li className="nav-list">Прайс</li>
      </ul>
    </header>
    <h1>Добро пожаловать в MonteBuild</h1>
    <h3 className="about-as-h3">Строительные и отделочные работы в Черногории</h3>
    <section className="contats">
      <div className="conacts-content">
        <ul>
          <li className="contact"><img className="icons" alt="logo" src="./img/local.png" width="30px"></img>Адрес :   Черногория , город Бар  </li>
          <li className="contact" ><img className="icons" alt="logo" src="./img/phone.png" width="30px"></img>Телефон : +38268479442</li>
          <li className="contact"> <img className="icons" alt="logo" src="./img/telegramm.png" width="30px"></img>Телеграмм  </li>
          <li className="contact" ><img className="icons" alt="logo" src="./img/facebook.png" width="30px"></img><a target="blanc" href="https://m.facebook.com/profile.php?id=100093278570439">Facebook</a>  </li>
          <li className="contact"> <img className="icons" alt="logo" src="./img/instagram.png" width="30px"></img>Instagramm  </li>
          <li className="contact"></li>

        </ul>
      </div>
      <div className="contacts-image">
        <img className="contacts-photo" src="./img/logo3.png" alt="logo"></img>
      </div>
    </section>
    <section className="about-us">
      
      <div className="about-as-content">
         <p>Хотите построить свою мечту на живописном побережье Черногории или осуществить ремонт своего существующего дома?<br></br> Мы готовы быть вашим надежным партнером в реализации ваших строительных проектов.</p>

        <h3>Профессионализм и качество</h3>
          <p>Мы сочетаем годы опыта с высококвалифицированными специалистами, чтобы обеспечить вам великолепное качество строительства. Наша команда экспертов в области строительства готова приступить к работе независимо от масштаба проекта.</p>

        <h3>Разнообразные услуги</h3>
        <p> Наша компания предоставляет широкий спектр услуг, которые включают:</p>
         <ul>
            <li>Строительство жилых и коммерческих помещений</li>
            <li>Реконструкция и ремонт</li>
            <li>Дизайн интерьера</li>
            <li>Электрические работы</li>
            <li>Сантехнические работы</li>
            <li>Индивидуальный подход</li>
          </ul>
          <p>Мы понимаем, что каждый проект уникален, поэтому мы готовы работать в близком сотрудничестве с вами, чтобы реализовать все ваши идеи. Наша команда поможет вам разработать план, выбрать материалы, контролировать бюджет и осуществить строительство в срок.</p>

        <h3>Удовлетворенность клиента</h3>
          <p>Ваше удовлетворение - наш главный приоритет. Мы стремимся предоставить вам надежные услуги высокого качества, соблюдая сроки и предлагая конкурентоспособные цены. Мы гордимся нашей репутацией надежного партнера в сфере строительства.</p>

        <h3>Связаться с нами</h3>
          <p>Сделайте первый шаг к воплощению своих строительных планов. Свяжитесь с нами сегодня, чтобы обсудить ваш проект, получить бесплатную консультацию и запросить смету на работы.</p>

          <p>Мы готовы помочь вам создать ваше идеальное место в Черногории!</p>
      </div>
      
    </section>
    
    </div>
  );
}

export default App;
