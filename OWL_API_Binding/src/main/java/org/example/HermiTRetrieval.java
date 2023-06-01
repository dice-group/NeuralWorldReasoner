package org.example;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.expression.OWLEntityChecker;
import org.semanticweb.owlapi.expression.ShortFormEntityChecker;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.HermiT.ReasonerFactory;
import org.semanticweb.owlapi.util.BidirectionalShortFormProvider;
import org.semanticweb.owlapi.util.BidirectionalShortFormProviderAdapter;
import org.semanticweb.owlapi.util.ShortFormProvider;
import org.semanticweb.owlapi.util.SimpleShortFormProvider;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLEntity;
import org.semanticweb.owlapi.model.OWLNamedIndividual;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.reasoner.Node;
import org.semanticweb.owlapi.reasoner.NodeSet;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.util.mansyntax.ManchesterOWLSyntaxParser;

import static org.semanticweb.owlapi.util.OWLAPIStreamUtils.asList;
import static org.semanticweb.owlapi.util.OWLAPIStreamUtils.asUnorderedSet;
import static spark.Spark.*;

public class HermiTRetrieval {
    /**
     * @param args args
     */
    private static final File file = new File("/home/demir/Desktop/Softwares/NRW/KGs/Family/family-benchmark_rich_background.owl");

    public static void main(String[] args) {
        //https://github.com/perwendel/spark
        port(8080);
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();

        OWLOntology ontology = null;
        try {
            ontology = manager.loadOntologyFromOntologyDocument(file);
        } catch (OWLOntologyCreationException e) {
            throw new RuntimeException(e);
        }
        System.out.println("Loaded ontology: " + ontology);

        DLQueryEngine dl=new DLQueryEngine(createReasoner(ontology), new SimpleShortFormProvider());

        post("/hermit", (request, response) -> {
            String cl=request.body().trim();
            Set<OWLNamedIndividual> individuals= dl.getInstances(cl, true);
            //JSONObject jo = new JSONObject();
            //jo.put("concept", cl);
            //jo.put("individuals", individuals);

            return individuals;
        });



    }

    private static void doQueryLoop(DLQueryPrinter dlQueryPrinter) throws IOException {
        while (true) {
            // Prompt the user to enter a class expression
            System.out.println(
                    "Please type a class expression in Manchester Syntax and press Enter (or press x to exit):");
            System.out.println("");
            String classExpression = readInput();
            // Check for exit condition
            if (classExpression.equalsIgnoreCase("x")) {
                break;
            }
            dlQueryPrinter.askQuery(classExpression.trim());
            System.out.println();
            System.out.println();
        }
    }
    private static String readInput() throws IOException {
        InputStream is = System.in;
        InputStreamReader reader;
        reader = new InputStreamReader(is, StandardCharsets.UTF_8);
        BufferedReader br = new BufferedReader(reader);
        return br.readLine();
    }

    private static OWLReasoner createReasoner(OWLOntology rootOntology) {
        // We need to create an instance of OWLReasoner. An OWLReasoner provides
        // the basic query functionality that we need, for example the ability
        // obtain the subclasses of a class etc. To do this we use a reasoner
        // factory.
        // Create a reasoner factory.

        //OWLReasonerFactory reasonerFactory = new StructuralReasonerFactory();
        OWLReasonerFactory reasonerFactory = new ReasonerFactory();
        return reasonerFactory.createReasoner(rootOntology);
    }
}
/**
 * This example shows how to perform a "dlquery". The DLQuery view/tab in Protege 4 works like this.
 */
class DLQueryEngine {

    private final OWLReasoner reasoner;
    private final DLQueryParser parser;

    /**
     * Constructs a DLQueryEngine. This will answer "DL queries" using the specified reasoner. A
     * short form provider specifies how entities are rendered.
     *
     * @param reasoner The reasoner to be used for answering the queries.
     * @param shortFormProvider A short form provider.
     */
    DLQueryEngine(OWLReasoner reasoner, ShortFormProvider shortFormProvider) {
        this.reasoner = reasoner;
        OWLOntology rootOntology = reasoner.getRootOntology();
        parser = new DLQueryParser(rootOntology, shortFormProvider);
    }

    /**
     * Gets the superclasses of a class expression parsed from a string.
     *
     * @param classExpressionString The string from which the class expression will be parsed.
     * @param direct Specifies whether direct superclasses should be returned or not.
     * @return The superclasses of the specified class expression If there was a problem parsing the
     *         class expression.
     */
    public Set<OWLClass> getSuperClasses(String classExpressionString, boolean direct) {
        if (classExpressionString.trim().isEmpty()) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser.parseClassExpression(classExpressionString);
        NodeSet<OWLClass> superClasses = reasoner.getSuperClasses(classExpression, direct);
        return asUnorderedSet(superClasses.entities());
    }

    /**
     * Gets the equivalent classes of a class expression parsed from a string.
     *
     * @param classExpressionString The string from which the class expression will be parsed.
     * @return The equivalent classes of the specified class expression If there was a problem
     *         parsing the class expression.
     */
    public Set<OWLClass> getEquivalentClasses(String classExpressionString) {
        if (classExpressionString.trim().isEmpty()) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser.parseClassExpression(classExpressionString);
        Node<OWLClass> equivalentClasses = reasoner.getEquivalentClasses(classExpression);
        return asUnorderedSet(
                equivalentClasses.entities().filter(cl -> !cl.equals(classExpression)));
    }

    /**
     * Gets the subclasses of a class expression parsed from a string.
     *
     * @param classExpressionString The string from which the class expression will be parsed.
     * @param direct Specifies whether direct subclasses should be returned or not.
     * @return The subclasses of the specified class expression If there was a problem parsing the
     *         class expression.
     */
    public Set<OWLClass> getSubClasses(String classExpressionString, boolean direct) {
        if (classExpressionString.trim().isEmpty()) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser.parseClassExpression(classExpressionString);
        NodeSet<OWLClass> subClasses = reasoner.getSubClasses(classExpression, direct);
        return asUnorderedSet(subClasses.entities());
    }

    /**
     * Gets the instances of a class expression parsed from a string.
     *
     * @param classExpressionString The string from which the class expression will be parsed.
     * @param direct Specifies whether direct instances should be returned or not.
     * @return The instances of the specified class expression If there was a problem parsing the
     *         class expression.
     */
    public Set<OWLNamedIndividual> getInstances(String classExpressionString, boolean direct) {
        if (classExpressionString.trim().isEmpty()) {
            return Collections.emptySet();
        }
        OWLClassExpression classExpression = parser.parseClassExpression(classExpressionString);
        NodeSet<OWLNamedIndividual> individuals = reasoner.getInstances(classExpression, direct);
        return asUnorderedSet(individuals.entities());
    }
}


class DLQueryParser {

    private final OWLOntology rootOntology;
    private final BidirectionalShortFormProvider bidiShortFormProvider;

    /**
     * Constructs a DLQueryParser using the specified ontology and short form provider to map entity
     * IRIs to short names.
     *
     * @param rootOntology The root ontology. This essentially provides the domain vocabulary for
     *        the query.
     * @param shortFormProvider A short form provider to be used for mapping back and forth between
     *        entities and their short names (renderings).
     */
    DLQueryParser(OWLOntology rootOntology, ShortFormProvider shortFormProvider) {
        this.rootOntology = rootOntology;
        OWLOntologyManager manager = rootOntology.getOWLOntologyManager();
        List<OWLOntology> importsClosure = asList(rootOntology.importsClosure());
        // Create a bidirectional short form provider to do the actual mapping.
        // It will generate names using the input
        // short form provider.
        bidiShortFormProvider =
                new BidirectionalShortFormProviderAdapter(manager, importsClosure, shortFormProvider);
    }

    /**
     * Parses a class expression string to obtain a class expression.
     *
     * @param classExpressionString The class expression string
     * @return The corresponding class expression if the class expression string is malformed or
     *         contains unknown entity names.
     */
    public OWLClassExpression parseClassExpression(String classExpressionString) {
        // Set up the real parser
        ManchesterOWLSyntaxParser parser = OWLManager.createManchesterParser();
        parser.setStringToParse(classExpressionString);
        parser.setDefaultOntology(rootOntology);
        // Specify an entity checker that wil be used to check a class
        // expression contains the correct names.
        OWLEntityChecker entityChecker = new ShortFormEntityChecker(bidiShortFormProvider);
        parser.setOWLEntityChecker(entityChecker);
        // Do the actual parsing
        return parser.parseClassExpression();
    }
}


class DLQueryPrinter {

    private final DLQueryEngine dlQueryEngine;
    private final ShortFormProvider shortFormProvider;

    /**
     * @param engine the engine
     * @param shortFormProvider the short form provider
     */
    DLQueryPrinter(DLQueryEngine engine, ShortFormProvider shortFormProvider) {
        this.shortFormProvider = shortFormProvider;
        dlQueryEngine = engine;
    }

    /**
     * @param classExpression the class expression to use for interrogation
     */
    public void askQuery(String classExpression) {
        if (classExpression.isEmpty()) {
            System.out.println("No class expression specified");
        } else {
            StringBuilder sb = new StringBuilder(1000);
            sb.append(
                    "\n--------------------------------------------------------------------------------\n");
            sb.append("QUERY:   ");
            sb.append(classExpression);
            sb.append('\n');
            sb.append(
                    "--------------------------------------------------------------------------------\n\n");
            // Ask for the subclasses, superclasses etc. of the specified
            // class expression. Print out the results.
            Set<OWLClass> superClasses = dlQueryEngine.getSuperClasses(classExpression, true);
            printEntities("SuperClasses", superClasses, sb);
            Set<OWLClass> equivalentClasses = dlQueryEngine.getEquivalentClasses(classExpression);
            printEntities("EquivalentClasses", equivalentClasses, sb);
            Set<OWLClass> subClasses = dlQueryEngine.getSubClasses(classExpression, true);
            printEntities("SubClasses", subClasses, sb);
            Set<OWLNamedIndividual> individuals = dlQueryEngine.getInstances(classExpression, true);
            printEntities("Instances", individuals, sb);
            System.out.println(sb);
        }
    }

    private void printEntities(String name, Set<? extends OWLEntity> entities, StringBuilder sb) {
        sb.append(name);
        int length = 50 - name.length();
        for (int i = 0; i < length; i++) {
            sb.append('.');
        }
        sb.append("\n\n");
        if (!entities.isEmpty()) {
            for (OWLEntity entity : entities) {
                sb.append('\t');
                sb.append(shortFormProvider.getShortForm(entity));
                sb.append('\n');
            }
        } else {
            sb.append("\t[NONE]\n");
        }
        sb.append('\n');
    }
}